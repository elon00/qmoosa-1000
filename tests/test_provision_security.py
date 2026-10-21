import importlib.util
from pathlib import Path
import tempfile
import unittest

WORK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provision", WORK / "tools/provision.py")
provision = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provision)


class ExportSecurityTests(unittest.TestCase):
    def test_export_omits_git_metadata_credentials_and_local_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("README.md", ".git/config", ".local/journal.json", ".env", ".env.production",
                         ".aws/credentials", "nested/credentials.json", "wallet.key", ".env.example"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")
            exported = provision.file_map(root)
            self.assertEqual(set(exported), {"README.md", ".env.example"})

    def test_symlink_cannot_export_a_file_outside_the_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / "project"
            project.mkdir()
            outside = root / "outside.txt"
            outside.write_text("private fixture\n", encoding="utf-8")
            try:
                (project / "linked.txt").symlink_to(outside)
            except OSError:
                self.skipTest("Symlink creation requires Windows privileges; exercised on Linux CI")
            with self.assertRaises(provision.q.Error):
                provision.file_map(project)


if __name__ == "__main__":
    unittest.main()
