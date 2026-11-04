"""Adversarial, offline evidence-integrity tests; no GitHub requests."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/verify_ci_evidence.py"
SPEC = importlib.util.spec_from_file_location("verify_ci_evidence", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
SHA = "a" * 40
OLD_SHA = "b" * 40


def repo():
    return {"name": "qmoosa-test-protocol", "repository_full_name": "elon00/qmoosa-test-protocol",
            "id": 123, "fork": False, "default_branch": "qmoosa-scaffold",
            "default_head_sha": SHA,
            "workflow_runs": [{"id": 77, "head_branch": "qmoosa-scaffold", "head_sha": SHA,
                               "status": "completed", "conclusion": "success",
                               "jobs": [{"status": "completed", "conclusion": "success"}]}]}


def audit(*snapshots):
    return checker.reconcile({"owner": "elon00", "target_total": 1,
                              "repositories": [{"name": "qmoosa-test-protocol"}]},
                             {"repositories": list(snapshots)})


class CiEvidenceTests(unittest.TestCase):
    def test_exact_default_head_and_jobs_pass(self):
        result = audit(repo())
        self.assertEqual((result["created_exact_nonfork"], result["ci_verified_current_default_head"]), (1, 1))
        self.assertEqual(result["ci_evidence_run_ids"], {"qmoosa-test-protocol": 77})
        self.assertIsNone(result["production_certified"])

    def test_historical_main_success_is_not_default_branch_success(self):
        r = repo()
        r["workflow_runs"][0]["head_branch"] = "main"
        self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_stale_commit_success_is_not_current_head(self):
        r = repo()
        r["workflow_runs"][0]["head_sha"] = OLD_SHA
        self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_failed_or_skipped_jobs_fail_closed(self):
        for conclusion in ("failure", "skipped", None):
            with self.subTest(conclusion=conclusion):
                r = repo()
                r["workflow_runs"][0]["jobs"][0]["conclusion"] = conclusion
                self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_missing_job_proof_does_not_count(self):
        r = repo()
        del r["workflow_runs"][0]["jobs"]
        self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_run_failure_or_incomplete_does_not_count(self):
        for key, value in (("conclusion", "failure"), ("status", "queued")):
            with self.subTest(key=key):
                r = repo()
                r["workflow_runs"][0][key] = value
                self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_redirected_or_forked_identity_is_not_created(self):
        for key, value in (("repository_full_name", "elon00/renamed"),
                           ("fork", True), ("id", 0)):
            with self.subTest(key=key):
                r = repo()
                r[key] = value
                self.assertEqual(audit(r)["created_exact_nonfork"], 0)

    def test_duplicate_repository_snapshot_cannot_inflate_counts(self):
        r = repo()
        result = audit(r, r.copy())
        self.assertEqual(result["created_exact_nonfork"], 0)
        self.assertEqual(len(result["rejected_evidence"]), 2)

    def test_same_stable_id_on_two_approved_names_rejects_both(self):
        first = repo()
        second = repo()
        second["name"] = "qmoosa-test-engine"
        second["repository_full_name"] = "elon00/qmoosa-test-engine"
        manifest = {"owner": "elon00", "target_total": 2,
                    "repositories": [{"name": "qmoosa-test-protocol"}, {"name": "qmoosa-test-engine"}]}
        result = checker.reconcile(manifest, {"repositories": [first, second]})
        self.assertEqual(result["created_exact_nonfork"], 0)

    def test_null_runs_fail_closed(self):
        r = repo()
        r["workflow_runs"] = None
        self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_no_head_sha_never_counts(self):
        r = repo()
        r["default_head_sha"] = "not-a-commit"
        self.assertEqual(audit(r)["ci_verified_current_default_head"], 0)

    def test_manifest_duplicates_rejected(self):
        manifest = {"owner": "elon00", "target_total": 2,
                    "repositories": [{"name": "x"}, {"name": "x"}]}
        with self.assertRaises(ValueError):
            checker.reconcile(manifest, {"repositories": []})

    def test_missing_snapshot_not_reported_created(self):
        result = audit()
        self.assertEqual(result["created_exact_nonfork"], 0)
        self.assertEqual(result["missing_or_unverified_names"], ["qmoosa-test-protocol"])


if __name__ == "__main__":
    unittest.main()
