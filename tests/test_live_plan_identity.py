"""Offline adversarial regression tests for live provisioning identity gates."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("qmoosa_live_identity", ROOT / "tools/qmoosa_engine.py")
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class LiveIdentityTests(unittest.TestCase):
    def manifest(self):
        return dict(schema_version=1, example=False, owner="elon00", target_total=1,
                    repositories=[dict(name="qmoosa-identity-fixture", description="Offline fixture",
                                       template="basic", private=True)])

    def repo(self, **overrides):
        row = dict(name="qmoosa-identity-fixture", id=101, private=True, fork=False,
                   owner={"login": "elon00"}, full_name="elon00/qmoosa-identity-fixture")
        row.update(overrides)
        return row

    def test_valid_exact_match_is_skipped_without_provisioning(self):
        plan = q.make_plan(self.manifest(), [self.repo()])
        self.assertEqual(plan["actions"][0]["action"], "skip")
        self.assertEqual(plan["actions"][0]["existing_id"], 101)
        self.assertEqual(q.check_plan(plan), q.validate(self.manifest()))

    def test_unrelated_owner_repo_is_not_a_canonical_match(self):
        other = self.repo(name="unrelated-repository", id=999, private=False, fork=True)
        plan = q.make_plan(self.manifest(), [other])
        self.assertEqual(plan["actions"][0]["action"], "create")

    def test_existing_public_repo_cannot_satisfy_private_default(self):
        with self.assertRaisesRegex(q.Error, "visibility mismatch"):
            q.make_plan(self.manifest(), [self.repo(private=False)])

    def test_existing_fork_is_rejected(self):
        with self.assertRaisesRegex(q.Error, "fork"):
            q.make_plan(self.manifest(), [self.repo(fork=True)])

    def test_duplicate_canonical_name_is_rejected(self):
        with self.assertRaisesRegex(q.Error, "Duplicate canonical"):
            q.make_plan(self.manifest(), [self.repo(), self.repo(id=102)])

    def test_invalid_or_duplicate_stable_ids_are_rejected(self):
        for bad in (None, 0, True, "101"):
            with self.subTest(id=bad), self.assertRaisesRegex(q.Error, "ID"):
                q.make_plan(self.manifest(), [self.repo(id=bad)])

    def test_missing_or_nonboolean_metadata_is_rejected(self):
        for field in ("private", "fork"):
            for bad in (None, "false", 0):
                with self.subTest(field=field, value=bad):
                    with self.assertRaisesRegex(q.Error, "nonboolean"):
                        q.make_plan(self.manifest(), [self.repo(**{field: bad})])

    def test_wrong_owner_and_full_name_are_rejected(self):
        with self.assertRaisesRegex(q.Error, "owner mismatch"):
            q.make_plan(self.manifest(), [self.repo(owner={"login": "other"})])
        with self.assertRaisesRegex(q.Error, "full_name mismatch"):
            q.make_plan(self.manifest(), [self.repo(full_name="other/qmoosa-identity-fixture")])

    def test_swapped_id_is_rejected_before_remote_write_or_journal(self):
        plan = q.make_plan(self.manifest(), [self.repo()])
        api = Mock()
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "state.json"
            with patch.object(q, "inventory", return_value=[self.repo(id=102)]):
                with self.assertRaisesRegex(q.Error, "drifted"):
                    q.apply_plan(plan, state, api, "elon00")
            self.assertFalse(state.exists())
        api.call.assert_not_called()

    def test_new_canonical_repo_after_plan_is_rejected(self):
        plan = q.make_plan(self.manifest(), [])
        api = Mock()
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "state.json"
            with patch.object(q, "inventory", return_value=[self.repo()]):
                with self.assertRaisesRegex(q.Error, "drifted"):
                    q.apply_plan(plan, state, api, "elon00")
            self.assertFalse(state.exists())
        api.call.assert_not_called()

    def test_unplanned_repo_after_inventory_check_stops_without_post(self):
        plan = q.make_plan(self.manifest(), [])
        api = Mock()
        api.call.return_value = self.repo()
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "state.json"
            with patch.object(q, "inventory", return_value=[]):
                with self.assertRaisesRegex(q.Error, "Unplanned repository appeared"):
                    q.apply_plan(plan, state, api, "elon00")
        self.assertEqual(api.call.call_count, 1)
        self.assertEqual(api.call.call_args.args[0], "GET")


if __name__ == "__main__":
    unittest.main()
