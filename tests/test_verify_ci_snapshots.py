"""Adversarial offline fixture tests; not live GitHub Actions evidence."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "verify_ci_snapshots", Path(__file__).resolve().parents[1] / "tools/verify_ci_snapshots.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
APPROVED = {"qmoosa-pqc-hybrid-tls-tests"}
SHA = "a" * 40
OLD = "b" * 40


def fixture():
    return {
        "repository": {"owner": {"login": "elon00"}, "id": 123,
                       "name": "qmoosa-pqc-hybrid-tls-tests",
                       "full_name": "elon00/qmoosa-pqc-hybrid-tls-tests",
                       "fork": False, "default_branch": "main"},
        "branch": {"name": "main", "commit": {"sha": SHA}},
        "required_workflows": ["Pinned Hybrid TLS Validation"],
        "runs": {"workflow_runs": [{"id": 100, "name": "Pinned Hybrid TLS Validation",
                                   "head_sha": SHA, "head_branch": "main", "event": "push",
                                   "status": "completed", "conclusion": "success"}]},
    }


class SnapshotTests(unittest.TestCase):
    def test_matching_current_head_push(self):
        r = mod.classify(fixture(), APPROVED)
        self.assertTrue(r["snapshot_ci_match"])
        self.assertFalse(r["independently_authenticated"])
        self.assertFalse(r["security_approved"])

    def test_stale_head_not_counted(self):
        s = fixture()
        s["runs"]["workflow_runs"][0]["head_sha"] = OLD
        self.assertFalse(mod.classify(s, APPROVED)["snapshot_ci_match"])

    def test_pr_head_not_counted(self):
        s = fixture()
        s["runs"]["workflow_runs"][0]["event"] = "pull_request"
        self.assertFalse(mod.classify(s, APPROVED)["snapshot_ci_match"])

    def test_non_default_branch_not_counted(self):
        s = fixture()
        s["runs"]["workflow_runs"][0]["head_branch"] = "audit/fix"
        self.assertFalse(mod.classify(s, APPROVED)["snapshot_ci_match"])

    def test_latest_failure_overrides_prior_success(self):
        s = fixture()
        s["runs"]["workflow_runs"].append({**s["runs"]["workflow_runs"][0], "id": 101, "conclusion": "failure"})
        self.assertFalse(mod.classify(s, APPROVED)["snapshot_ci_match"])

    def test_missing_required_workflow(self):
        s = fixture()
        s["required_workflows"].append("CodeQL")
        self.assertFalse(mod.classify(s, APPROVED)["snapshot_ci_match"])

    def test_unrelated_repo_rejected(self):
        s = fixture()
        s["repository"]["name"] = "unrelated"
        s["repository"]["full_name"] = "elon00/unrelated"
        with self.assertRaises(mod.SnapshotError):
            mod.classify(s, APPROVED)

    def test_fork_rejected(self):
        s = fixture()
        s["repository"]["fork"] = True
        with self.assertRaises(mod.SnapshotError):
            mod.classify(s, APPROVED)

    def test_owner_rejected(self):
        s = fixture()
        s["repository"]["owner"]["login"] = "someoneelse"
        with self.assertRaises(mod.SnapshotError):
            mod.classify(s, APPROVED)

    def test_wrong_branch_response_rejected(self):
        s = fixture()
        s["branch"]["name"] = "not-main"
        with self.assertRaises(mod.SnapshotError):
            mod.classify(s, APPROVED)

    def test_missing_fork_field_rejected(self):
        s = fixture()
        del s["repository"]["fork"]
        with self.assertRaises(mod.SnapshotError):
            mod.classify(s, APPROVED)

    def test_missing_required_list_rejected(self):
        s = fixture()
        s["required_workflows"] = []
        with self.assertRaises(mod.SnapshotError):
            mod.classify(s, APPROVED)

    def test_incomplete_run_not_counted(self):
        s = fixture()
        s["runs"]["workflow_runs"][0]["status"] = "in_progress"
        self.assertFalse(mod.classify(s, APPROVED)["snapshot_ci_match"])


if __name__ == "__main__":
    unittest.main()
