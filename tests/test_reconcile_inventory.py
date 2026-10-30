"""Offline adversarial tests; fixtures are not live GitHub evidence."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "reconcile_inventory", Path(__file__).resolve().parents[1] / "tools/reconcile_inventory.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def manifest():
    return {"domains": [{"batches": [{"repositories": [
        {"name": f"qmoosa-approved-{i:04d}"} for i in range(1000)]}]}]}


def repo(name="qmoosa-approved-0000", rid=123, owner="elon00", fork=False):
    return {"id": rid, "name": name, "full_name": owner + "/" + name,
            "owner": {"login": owner}, "fork": fork}


class ReconcileTests(unittest.TestCase):
    def test_exact_match_only(self):
        r = mod.reconcile(manifest(), [repo(), repo("not-approved", 124)])
        self.assertEqual(r["created_exact_observed_lower_bound"], 1)
        self.assertEqual(r["other_owned_original_repos_excluded"], ["not-approved"])
        self.assertFalse(r["inventory_complete"])

    def test_fork_excluded(self):
        r = mod.reconcile(manifest(), [repo(fork=True)])
        self.assertEqual(r["created_exact_observed_lower_bound"], 0)
        self.assertEqual(r["excluded_fork_records"], 1)

    def test_unrelated_owner_excluded(self):
        r = mod.reconcile(manifest(), [repo(owner="other")])
        self.assertEqual(r["created_exact_observed_lower_bound"], 0)
        self.assertEqual(r["excluded_other_owner_records"], 1)

    def test_duplicate_same_identity_deduped(self):
        r = mod.reconcile(manifest(), [repo(), repo()])
        self.assertEqual(r["created_exact_observed_lower_bound"], 1)

    def test_duplicate_name_different_id_rejected(self):
        with self.assertRaises(mod.InventoryError):
            mod.reconcile(manifest(), [repo(), repo(rid=125)])

    def test_duplicate_id_different_name_rejected(self):
        with self.assertRaises(mod.InventoryError):
            mod.reconcile(manifest(), [repo(), repo("qmoosa-approved-0001")])

    def test_mismatched_full_name_rejected(self):
        bad = repo()
        bad["full_name"] = "other/" + bad["name"]
        with self.assertRaises(mod.InventoryError):
            mod.reconcile(manifest(), [bad])

    def test_missing_fork_rejected(self):
        bad = repo()
        del bad["fork"]
        with self.assertRaises(mod.InventoryError):
            mod.reconcile(manifest(), [bad])

    def test_manifest_duplicate_rejected(self):
        m = manifest()
        m["domains"][0]["batches"][0]["repositories"][1]["name"] = "qmoosa-approved-0000"
        with self.assertRaises(mod.InventoryError):
            mod.approved_names(m)

    def test_json_pages_and_jsonl(self):
        import json
        data = [repo(), repo("qmoosa-approved-0001", 124)]
        self.assertEqual(mod.load_inventory(json.dumps([data])), data)
        self.assertEqual(mod.load_inventory("\n".join(map(json.dumps, data))), data)

    def test_no_claimed_certification(self):
        r = mod.reconcile(manifest(), [repo()])
        for key in ("implemented", "current_head_ci_verified", "security_approved",
                    "deployment_ready", "production_certified"):
            self.assertEqual(r[key], "not_verified")


if __name__ == "__main__":
    unittest.main()
