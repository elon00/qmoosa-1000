#!/usr/bin/env python3
"""Pinned local credential scanning. Never changes repository visibility."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

WORK = Path(__file__).resolve().parents[1]
VERSION = "8.30.1"
ASSETS = {
    "Windows": ("windows_x64.zip", "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e", "gitleaks.exe"),
    "Linux": ("linux_x64.tar.gz", "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb", "gitleaks"),
}
SAFE_FIELDS = ("RuleID", "File", "StartLine", "Commit", "Fingerprint")
MAX_REVIEW_ARCHIVE_BYTES = 30 * 1024 * 1024
MAX_REVIEW_MEMBER_BYTES = 16 * 1024 * 1024
MAX_REVIEW_ARCHIVE_DEPTH = 3


def run(args, *, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} returned {result.returncode}; command output withheld")
    return result.stdout


def asset():
    if platform.machine().lower() not in ("amd64", "x86_64") or platform.system() not in ASSETS:
        raise RuntimeError("The pinned installer currently supports Windows x64 and Linux x64")
    return ASSETS[platform.system()]


def unpack(data):
    suffix, checksum, executable = asset()
    if len(data) > 30 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != checksum:
        raise RuntimeError("Official scanner archive checksum mismatch")
    if suffix.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            if bundle.getinfo(executable).file_size > 60 * 1024 * 1024:
                raise RuntimeError("Unexpected executable size")
            return bundle.read(executable)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as bundle:
        member = bundle.getmember(executable)
        if not member.isfile() or member.size > 60 * 1024 * 1024:
            raise RuntimeError("Unexpected executable entry")
        return bundle.extractfile(member).read()


def install():
    suffix, _, executable = asset()
    url = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/gitleaks_{VERSION}_{suffix}"
    request = urllib.request.Request(url, headers={"User-Agent": "qmoosa-security-guard"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive = response.read(30 * 1024 * 1024 + 1)
    program = unpack(archive)
    folder = WORK / ".local/security"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / suffix).write_bytes(archive)
    target = folder / executable
    target.write_bytes(program)
    target.chmod(0o700)
    print(f"Installed checksum-verified Gitleaks {VERSION}")


def scanner():
    suffix, _, executable = asset()
    folder = WORK / ".local/security"
    archive = folder / suffix
    target = folder / executable
    if not archive.is_file() or not target.is_file():
        raise RuntimeError("Run: python tools/security_guard.py install")
    # Verify against the pinned archive again, never against a self-authored receipt.
    expected = unpack(archive.read_bytes())
    if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(expected).digest():
        raise RuntimeError("Installed scanner differs from its checksum-verified archive")
    return target


def git(repo, *args):
    return run(["git", "-C", str(repo), *args])


def review_blob_id(repo, path, commit, staged):
    """Resolve an exact literal Git filename without reading its blob body."""
    command = (["ls-files", "--stage", "-z", "--", path] if staged else
               ["ls-tree", "-r", "-z", "--full-tree", commit, "--", path])
    records = git(repo, "--literal-pathspecs", *command).split(b"\0")
    matches = [record.split(b"\t", 1)[0].split() for record in records
               if b"\t" in record and record.split(b"\t", 1)[1] == path.encode("utf-8")]
    if not matches:
        return None
    if len(matches) != 1 or len(matches[0]) != 3:
        raise RuntimeError("Ambiguous Git source cannot receive a review")
    fields = matches[0]
    if fields[0] not in (b"100644", b"100755", b"120000") or (
            fields[2] != b"0" if staged else fields[1] != b"blob"):
        raise RuntimeError("Git source is not an unambiguous file blob")
    object_id = fields[1 if staged else 2].decode("ascii")
    if len(object_id) not in (40, 64) or any(c not in "0123456789abcdef" for c in object_id):
        raise RuntimeError("Unexpected Git object identity")
    return object_id


def review_blob(repo, object_id):
    """Check size, then read the same immutable blob without text conversion."""
    declared = git(repo, "cat-file", "-s", object_id).strip()
    if not declared.isdigit() or int(declared) > MAX_REVIEW_ARCHIVE_BYTES:
        raise RuntimeError("Reviewed Git blob exceeds the supported size bound")
    content = git(repo, "cat-file", "blob", object_id)
    if len(content) != int(declared):
        raise RuntimeError("Git source size changed unexpectedly")
    return content


def review_source(repo, path, commit, staged):
    """Read exact Git/index bytes and bounded ZIP members without extraction.

    Archive approvals bind both the whole outer Git blob and the leaf source.
    Ambiguous/unsafe entries cannot receive a reviewed-fixture exception.
    """
    # A literal filename containing ! takes precedence over archive notation.
    object_id = review_blob_id(repo, path, commit, staged)
    if object_id is not None:
        return review_blob(repo, object_id), None
    parts = path.split("!")
    if len(parts) - 1 > MAX_REVIEW_ARCHIVE_DEPTH:
        raise RuntimeError("Reviewed archive nesting exceeds the supported bound")
    for boundary in range(len(parts) - 1, 0, -1):
        object_id = review_blob_id(repo, "!".join(parts[:boundary]), commit, staged)
        if object_id is not None:
            members = parts[boundary:]
            break
    else:
        raise RuntimeError("Reviewed Git source could not be resolved")
    content = review_blob(repo, object_id)
    container_hash = hashlib.sha256(content).hexdigest()
    try:
        for member in members:
            parts = PurePosixPath(member).parts
            if (not member or member.startswith("/") or "\\" in member or ":" in member
                    or any(part in (".", "..") for part in parts)
                    or str(PurePosixPath(member)) != member
                    or len(content) > MAX_REVIEW_ARCHIVE_BYTES):
                raise ValueError("Unsafe or oversized archive review source")
            with zipfile.ZipFile(io.BytesIO(content)) as bundle:
                entries = [item for item in bundle.infolist() if item.filename == member]
                if len(entries) != 1:
                    raise ValueError("Missing or ambiguous archive member")
                entry = entries[0]
                kind = stat.S_IFMT(entry.external_attr >> 16)
                if (entry.is_dir() or kind not in (0, stat.S_IFREG)
                        or entry.file_size > MAX_REVIEW_MEMBER_BYTES):
                    raise ValueError("Unsupported archive member")
                with bundle.open(entry) as stream:
                    content = stream.read(MAX_REVIEW_MEMBER_BYTES + 1)
                if len(content) != entry.file_size or len(content) > MAX_REVIEW_MEMBER_BYTES:
                    raise ValueError("Incomplete or oversized archive member")
    except (OSError, ValueError, KeyError, RuntimeError, EOFError,
            NotImplementedError, zipfile.BadZipFile):
        raise RuntimeError("Archived review source could not be verified safely") from None
    return content, container_hash


def reviewed(repo, finding, approvals, staged):
    """Accept a review only for identical leaf bytes and container identity."""
    candidates = [entry for entry in approvals if entry["rule"] == finding.get("RuleID")
                  and entry["path"] == finding.get("File") and entry["line"] == finding.get("StartLine")]
    if not candidates:
        return False
    commit = finding.get("Commit", "")
    content, container_hash = review_source(repo, finding["File"], commit, staged)
    digest = hashlib.sha256(content).hexdigest()
    return any(entry["blob_sha256"] == digest
               and entry.get("container_sha256") == container_hash
               for entry in candidates)


def scan(repo, report_path):
    repo = Path(repo).resolve(strict=True)
    if git(repo, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise RuntimeError("Full history is required; use a full clone or fetch the missing history first")
    executable = scanner()
    policy = WORK / "tools/security-policy.toml"
    approvals = json.loads((WORK / "tools/reviewed-test-fixtures.json").read_text(encoding="utf-8"))["entries"]
    before_refs = git(repo, "for-each-ref", "--format=%(objectname) %(refname)")
    bare = git(repo, "rev-parse", "--is-bare-repository").strip() == b"true"
    before_index = b"" if bare else git(repo, "diff", "--cached", "--raw", "-z", "--no-renames")
    findings, reviewed_findings = [], []
    with tempfile.TemporaryDirectory(prefix="qmoosa-scan-") as temporary:
        ignored = Path(temporary) / "empty.gitleaksignore"
        ignored.write_text("", encoding="utf-8")
        metadata = git(repo, "log", "--all", "--format=commit %H%n%B") + b"\n" + git(
            repo, "for-each-ref", "refs/tags", "--format=tag %(objectname)%0a%(contents)")
        scopes = ["history", "metadata"] + ([] if bare else ["staged"])
        for scope in scopes:
            staged = scope == "staged"
            result_path = Path(temporary) / (scope + ".json")
            mode = ["--pre-commit", "--staged"] if staged else ["--log-opts=--all --full-history -m"]
            source = ["stdin"] if scope == "metadata" else ["git", str(repo), *mode]
            command = [str(executable), *source, "--config", str(policy),
                       "--gitleaks-ignore-path", str(ignored), "--ignore-gitleaks-allow", "--redact=100",
                       "--no-banner", "--no-color", "--max-decode-depth=5", "--max-archive-depth=3",
                       "--timeout=120", "--report-format=json", "--report-path", str(result_path)]
            completed = subprocess.run(command, input=metadata if scope == "metadata" else None,
                                       capture_output=True, timeout=150)
            if completed.returncode not in (0, 1) or not result_path.is_file():
                raise RuntimeError("Credential scan failed; no clean result is claimed")
            detected = json.loads(result_path.read_text(encoding="utf-8"))
            if not isinstance(detected, list) or completed.returncode != (1 if detected else 0):
                raise RuntimeError("Scanner result/exit-code mismatch")
            for finding in detected:
                safe = {field: finding.get(field) for field in SAFE_FIELDS}
                if scope == "metadata":
                    safe["File"] = "<commit-and-tag-messages>"
                    findings.append(safe)
                else:
                    (reviewed_findings if reviewed(repo, safe, approvals, staged) else findings).append(safe)
    if before_refs != git(repo, "for-each-ref", "--format=%(objectname) %(refname)"):
        raise RuntimeError("Git refs changed during the scan")
    if not bare and before_index != git(repo, "diff", "--cached", "--raw", "-z", "--no-renames"):
        raise RuntimeError("Staged content changed during the scan")
    report = {"scanner": f"gitleaks {VERSION}", "status": "blocked" if findings else "passed",
              "scope": "available local Git history including merge diffs, commit/tag messages and staged changes; not hosted logs or other GitHub surfaces",
              "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
              "findings": findings, "reviewed_test_findings": reviewed_findings}
    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Credential scan {report['status']}; unresolved findings={len(findings)}; redacted report: {report_path}")
    return 1 if findings else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install", help="Download and verify the fixed official scanner")
    command = sub.add_parser("scan", help="Scan complete local history and staged changes")
    command.add_argument("--repo", default=".")
    command.add_argument("--report", default=str(WORK / ".local/security/report.json"))
    args = parser.parse_args()
    if args.command == "install":
        install()
        return 0
    return scan(args.repo, args.report)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        raise SystemExit(2)
