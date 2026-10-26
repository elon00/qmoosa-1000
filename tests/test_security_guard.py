import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import secrets
import subprocess
import tempfile
import unittest
import warnings
import zipfile
from unittest.mock import patch

WORK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("security_guard", WORK / "tools/security_guard.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class CredentialGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="qmoosa-guard-test-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        guard.run(["git", "init", "-q", str(self.repo)])
        guard.git(self.repo, "config", "user.name", "Security fixture")
        guard.git(self.repo, "config", "user.email", "fixture@example.invalid")

    def tearDown(self):
        self.temp.cleanup()

    def commit(self):
        guard.git(self.repo, "add", "--all")
        guard.git(self.repo, "-c", "user.name=Security fixture", "-c", "user.email=fixture@example.invalid",
                  "commit", "-qm", "fixture")

    def assert_detected_without_disclosure(self, credential):
        report = self.root / "report.json"
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = guard.scan(self.repo, report)
        self.assertEqual(result, 1)
        self.assertTrue(json.loads(report.read_text(encoding="utf-8"))["findings"])
        self.assertNotIn(credential, output.getvalue())
        self.assertNotIn(credential.encode(), report.read_bytes())
        self.assertNotIn('"Secret":', report.read_text(encoding="utf-8"))

    def test_deleted_credential_is_found_despite_repository_suppressions(self):
        credential = "ghp_" + secrets.token_hex(18)
        (self.repo / "config.js").write_text("const apiKey='" + credential + "'; // gitleaks:allow\n", encoding="utf-8")
        (self.repo / ".gitleaks.toml").write_text('[allowlist]\nregexes=[\'.*\']\n', encoding="utf-8")
        self.commit()
        (self.repo / "config.js").unlink()
        self.commit()
        self.assert_detected_without_disclosure(credential)

    def test_staged_credential_is_found_before_commit(self):
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.commit()
        credential = "ghp_" + secrets.token_hex(18)
        (self.repo / "config.js").write_text("const apiKey='" + credential + "';\n", encoding="utf-8")
        guard.git(self.repo, "add", "config.js")
        self.assert_detected_without_disclosure(credential)

    def test_shallow_history_is_rejected(self):
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.commit()
        clone = self.root / "shallow"
        guard.run(["git", "clone", "--depth", "1", self.repo.as_uri(), str(clone)])
        with self.assertRaisesRegex(RuntimeError, "Full history"):
            guard.scan(clone, self.root / "report.json")

    def test_credential_added_only_in_merge_commit_is_detected(self):
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.commit()
        initial = guard.git(self.repo, "branch", "--show-current").decode().strip()
        guard.git(self.repo, "checkout", "-qb", "other")
        (self.repo / "other.txt").write_text("branch\n", encoding="utf-8")
        self.commit()
        guard.git(self.repo, "checkout", initial)
        guard.git(self.repo, "merge", "--no-ff", "--no-commit", "other")
        credential = "ghp_" + secrets.token_hex(18)
        (self.repo / "config.js").write_text("const apiKey='" + credential + "';\n", encoding="utf-8")
        self.commit()
        (self.repo / "config.js").unlink()
        self.commit()
        self.assert_detected_without_disclosure(credential)

    def test_commit_message_credential_is_detected(self):
        credential = "ghp_" + secrets.token_hex(18)
        guard.git(self.repo, "-c", "user.name=Security fixture", "-c", "user.email=fixture@example.invalid",
                  "commit", "--allow-empty", "-qm", "api_key=" + credential)
        self.assert_detected_without_disclosure(credential)

    def test_annotated_tag_message_credential_is_detected(self):
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.commit()
        credential = "ghp_" + secrets.token_hex(18)
        guard.git(self.repo, "-c", "user.name=Security fixture", "-c", "user.email=fixture@example.invalid",
                  "tag", "-a", "fixture", "-m", "api_key=" + credential)
        self.assert_detected_without_disclosure(credential)

    def test_archive_tampering_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "checksum"):
            guard.unpack(b"not the trusted archive")

    def test_installed_binary_tampering_is_rejected(self):
        suffix, _, executable = guard.asset()
        archive = (WORK / ".local/security" / suffix).read_bytes()
        cache = self.root / ".local/security"
        cache.mkdir(parents=True)
        (cache / suffix).write_bytes(archive)
        (cache / executable).write_bytes(b"untrusted executable fixture")
        with patch.object(guard, "WORK", self.root), self.assertRaisesRegex(RuntimeError, "differs"):
            guard.scanner()

    def test_fixture_review_requires_exact_file_content(self):
        path = self.repo / "negative-test.js"
        path.write_text("const url='https://" + "user:password" + "@example.com';\n", encoding="utf-8", newline="\n")
        self.commit()
        finding = {"RuleID": "qmoosa-credential-url", "File": path.name, "StartLine": 1,
                   "Commit": guard.git(self.repo, "rev-parse", "HEAD").decode().strip()}
        approvals = [{"rule": finding["RuleID"], "path": path.name, "line": 1,
                      "blob_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]
        self.assertTrue(guard.reviewed(self.repo, finding, approvals, False))
        path.write_text(path.read_text(encoding="utf-8") + "// modified fixture\n", encoding="utf-8", newline="\n")
        self.commit()
        finding["Commit"] = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        self.assertFalse(guard.reviewed(self.repo, finding, approvals, False))

    def archive(self, entries):
        """Build ZIP bytes in memory, including deliberately invalid fixtures."""
        output = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
                for name, content in entries:
                    bundle.writestr(name, content)
        return output.getvalue()

    def zip_fixture(self, content=b"public test fixture\n", member="src/fixture.js"):
        """Commit a ZIP fixture and record its exact leaf and container hashes."""
        archive = self.archive([(member, content)])
        (self.repo / "fixture.zip").write_bytes(archive)
        self.commit()
        finding = {"RuleID": "qmoosa-credential-assignment", "File": "fixture.zip!" + member,
                   "StartLine": 1, "Commit": guard.git(self.repo, "rev-parse", "HEAD").decode().strip()}
        approval = {"rule": finding["RuleID"], "path": finding["File"], "line": 1,
                    "blob_sha256": hashlib.sha256(content).hexdigest(),
                    "container_sha256": hashlib.sha256(archive).hexdigest()}
        return finding, approval

    def test_zip_review_requires_exact_container_and_leaf_hashes(self):
        """Both hashes are mandatory; missing or incorrect hashes reject review."""
        finding, approval = self.zip_fixture()
        self.assertTrue(guard.reviewed(self.repo, finding, [approval], False))
        for field in ("container_sha256", "blob_sha256"):
            wrong = {**approval, field: "0" * 64}
            self.assertFalse(guard.reviewed(self.repo, finding, [wrong], False))
        missing = {key: value for key, value in approval.items() if key != "container_sha256"}
        self.assertFalse(guard.reviewed(self.repo, finding, [missing], False))

    def test_zip_change_cannot_inherit_a_review_even_with_same_leaf(self):
        """An outer archive change invalidates a review of an unchanged member."""
        finding, approval = self.zip_fixture()
        changed = self.archive([("src/fixture.js", b"public test fixture\n"), ("extra.txt", b"new content")])
        (self.repo / "fixture.zip").write_bytes(changed)
        self.commit()
        finding["Commit"] = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        self.assertFalse(guard.reviewed(self.repo, finding, [approval], False))

    def test_nested_zip_review_binds_outer_archive_and_leaf(self):
        """Nested reviews bind the outer Git blob and the final source member."""
        leaf = b"public nested test fixture\n"
        nested = self.archive([("src/fixture.js", leaf)])
        outer = self.archive([("inner.zip", nested)])
        (self.repo / "fixture.zip").write_bytes(outer)
        self.commit()
        commit = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        finding = {"RuleID": "qmoosa-credential-assignment", "File": "fixture.zip!inner.zip!src/fixture.js",
                   "StartLine": 1, "Commit": commit}
        approval = {"rule": finding["RuleID"], "path": finding["File"], "line": 1,
                    "blob_sha256": hashlib.sha256(leaf).hexdigest(),
                    "container_sha256": hashlib.sha256(outer).hexdigest()}
        self.assertTrue(guard.reviewed(self.repo, finding, [approval], False))
        approval["blob_sha256"] = hashlib.sha256(nested).hexdigest()
        self.assertFalse(guard.reviewed(self.repo, finding, [approval], False))

    def test_credential_in_nested_zip_is_detected_without_disclosure(self):
        """Nested archive scanning detects a canary without exposing its value."""
        credential = "ghp_" + secrets.token_hex(18)
        nested = self.archive([("src/config.js", ("const apiKey='" + credential + "';\n").encode())])
        (self.repo / "fixture.zip").write_bytes(self.archive([("inner.zip", nested)]))
        self.commit()
        self.assert_detected_without_disclosure(credential)

    def test_staged_zip_review_uses_index_not_working_tree(self):
        """Unstaged filesystem changes cannot replace reviewed index content."""
        finding, approval = self.zip_fixture()
        guard.git(self.repo, "add", "fixture.zip")
        (self.repo / "fixture.zip").write_bytes(b"unstaged content")
        self.assertTrue(guard.reviewed(self.repo, finding, [approval], True))

    def test_duplicate_and_unsafe_zip_members_are_rejected(self):
        """Ambiguous names and unsafe paths cannot receive archive exceptions."""
        for member in ("../fixture.js", "/fixture.js", "a/../fixture.js", "a\\fixture.js"):
            finding, approval = self.zip_fixture(member=member)
            with self.assertRaisesRegex(RuntimeError, "safely"):
                guard.reviewed(self.repo, finding, [approval], False)
        finding, approval = self.zip_fixture()
        (self.repo / "fixture.zip").write_bytes(self.archive([
            ("src/fixture.js", b"first"), ("src/fixture.js", b"second")]))
        self.commit()
        finding["Commit"] = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        with self.assertRaisesRegex(RuntimeError, "safely"):
            guard.reviewed(self.repo, finding, [approval], False)

    def test_review_archive_size_and_nesting_bounds(self):
        """Oversized members and excessive nesting remain unresolved."""
        finding, approval = self.zip_fixture(content=b"x" * 129)
        with patch.object(guard, "MAX_REVIEW_MEMBER_BYTES", 128), self.assertRaisesRegex(RuntimeError, "safely"):
            guard.reviewed(self.repo, finding, [approval], False)
        finding["File"] = "fixture.zip!a.zip!b.zip!c.zip!fixture.js"
        with self.assertRaisesRegex(RuntimeError, "nesting"):
            guard.review_source(self.repo, finding["File"], finding["Commit"], False)

    def test_symlink_archive_member_cannot_receive_an_exception(self):
        """A ZIP symlink entry is rejected instead of treated as source bytes."""
        output = io.BytesIO()
        entry = zipfile.ZipInfo("src/fixture.js")
        entry.create_system = 3
        entry.external_attr = (0o120777 << 16)
        with zipfile.ZipFile(output, "w") as bundle:
            bundle.writestr(entry, "../outside")
        (self.repo / "fixture.zip").write_bytes(output.getvalue())
        self.commit()
        commit = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        with self.assertRaisesRegex(RuntimeError, "safely"):
            guard.review_source(self.repo, "fixture.zip!src/fixture.js", commit, False)

    def test_oversized_git_blob_is_rejected_before_reading_its_body(self):
        """Reject an oversized Git blob using metadata before requesting bytes."""
        finding, approval = self.zip_fixture()
        original = guard.git
        body_reads = []

        def observed(repo, *args):
            if args[:2] == ("cat-file", "blob"):
                body_reads.append(args[2])
            return original(repo, *args)

        with patch.object(guard, "MAX_REVIEW_ARCHIVE_BYTES", 1), patch.object(guard, "git", side_effect=observed):
            with self.assertRaisesRegex(RuntimeError, "size bound"):
                guard.reviewed(self.repo, finding, [approval], False)
        self.assertEqual(body_reads, [])

    def test_staged_blob_identity_cannot_change_between_size_and_body_read(self):
        """A concurrent index change cannot substitute the size-checked object."""
        finding, approval = self.zip_fixture()
        original = guard.git
        changed = False

        def change_index_after_size(repo, *args):
            nonlocal changed
            result = original(repo, *args)
            if args[:2] == ("cat-file", "-s") and not changed:
                changed = True
                (self.repo / "fixture.zip").write_bytes(self.archive([("src/fixture.js", b"new index fixture\n")]))
                original(repo, "add", "fixture.zip")
            return result

        with patch.object(guard, "git", side_effect=change_index_after_size):
            content, container_hash = guard.review_source(self.repo, finding["File"], finding["Commit"], True)
        self.assertTrue(changed)
        self.assertEqual(content, b"public test fixture\n")
        self.assertEqual(container_hash, approval["container_sha256"])
        self.assertFalse(guard.reviewed(self.repo, finding, [approval], True))

    def test_literal_exclamation_filename_is_not_interpreted_as_a_zip(self):
        """Literal Git filenames with exclamation marks retain their identity."""
        path = "literal!fixture!with!several!marks.js"
        content = b"public literal-name fixture\n"
        (self.repo / path).write_bytes(content)
        self.commit()
        commit = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        for staged in (False, True):
            actual, container_hash = guard.review_source(self.repo, path, commit, staged)
            self.assertEqual(actual, content)
            self.assertIsNone(container_hash)

    def test_literal_filename_collision_cannot_inherit_an_archive_review(self):
        """A real file colliding with archive notation cannot borrow its review."""
        finding, approval = self.zip_fixture()
        literal = self.repo / finding["File"]
        literal.parent.mkdir(parents=True)
        literal.write_bytes(b"different literal Git file\n")
        self.commit()
        finding["Commit"] = guard.git(self.repo, "rev-parse", "HEAD").decode().strip()
        self.assertFalse(guard.reviewed(self.repo, finding, [approval], False))
        content, container_hash = guard.review_source(self.repo, finding["File"], finding["Commit"], False)
        self.assertEqual(content, literal.read_bytes())
        self.assertIsNone(container_hash)


if __name__ == "__main__":
    unittest.main()
