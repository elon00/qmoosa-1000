import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

WORK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("account_security", WORK / "tools/account_security.py")
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)


class AccountControlTests(unittest.TestCase):
    def setUp(self):
        control.STOP.clear()
        self.repo = {"id": 1, "name": "fixture", "full_name": "elon00/fixture"}
        self.metadata = {**self.repo, "owner": {"login": "elon00"}, "private": False,
                         "permissions": {"admin": True}, "security_and_analysis": {}}

    def test_private_repository_is_never_published_or_reconfigured(self):
        self.metadata["private"] = True
        with patch.object(control, "api", return_value=self.metadata) as api:
            result = control.harden(self.repo, "elon00", True)
        self.assertEqual(result["status"], "private_held")
        self.assertEqual(api.call_count, 1)

    def test_preview_does_not_write_settings(self):
        with patch.object(control, "api", return_value=self.metadata) as api:
            result = control.harden(self.repo, "elon00", False)
        self.assertEqual(result["status"], "needs_changes")
        self.assertEqual(api.call_count, 1)

    def test_apply_only_enables_the_two_public_secret_controls(self):
        final = {**self.metadata, "security_and_analysis": {key: {"status": "enabled"} for key in control.CONTROLS}}
        with patch.object(control, "api", side_effect=[self.metadata, final]) as api:
            result = control.harden(self.repo, "elon00", True)
        self.assertEqual(result["status"], "protected")
        self.assertEqual(api.call_args.kwargs["body"], {"security_and_analysis": {
            "secret_scanning": {"status": "enabled"}, "secret_scanning_push_protection": {"status": "enabled"}}})

    def test_owner_change_prevents_mutation(self):
        self.metadata["owner"]["login"] = "another-owner"
        with patch.object(control, "api", return_value=self.metadata) as api:
            result = control.harden(self.repo, "elon00", True)
        self.assertEqual(result["status"], "requires_review")
        self.assertEqual(api.call_count, 1)

    def test_missing_security_metadata_does_not_claim_protection(self):
        self.metadata["security_and_analysis"] = None
        with patch.object(control, "api", return_value=self.metadata):
            result = control.harden(self.repo, "elon00", False)
        self.assertEqual(result["status"], "needs_changes")
        self.assertTrue(all(value == "unknown" for value in result["previous"].values()))


if __name__ == "__main__":
    unittest.main()
