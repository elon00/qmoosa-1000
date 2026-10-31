"""Prevent excluded asset manifests from reaching planning or provisioning."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("asset_scope_engine", ROOT / "tools/qmoosa_engine.py")
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class AssetScopeTests(unittest.TestCase):
    def manifest(self):
        return dict(schema_version=1, owner="elon00", target_total=1,
                    repositories=[dict(name="crypto-token-interop", description="Cryptocurrency token interoperability",
                                       template="basic", private=True)])

    def test_excluded_asset_spellings_in_project_fields(self):
        for text in ("cbdcbridge", "CBCD", "Central Bank Digital Currency", "central-bank-digital-currencies", "digital_rupee"):
            for field in ("name", "description", "template"):
                with self.subTest(text=text, field=field):
                    manifest = self.manifest()
                    manifest["repositories"][0][field] = text.lower().replace(" ", "-") if field == "name" else text
                    with self.assertRaisesRegex(q.Error, "excluded"):
                        q.validate(manifest)
                    with self.assertRaisesRegex(q.Error, "excluded"):
                        q.make_plan(manifest)

    def test_owner_is_also_checked(self):
        manifest = self.manifest()
        manifest["owner"] = "cbdc-owner"
        with self.assertRaisesRegex(q.Error, "excluded"):
            q.validate(manifest)

    def test_rehashed_plan_cannot_bypass_scope(self):
        plan = q.make_plan(self.manifest())
        plan["manifest"]["repositories"][0]["description"] = "CBDC integration"
        plan["plan_id"] = q.digest({k: v for k, v in plan.items() if k != "plan_id"})
        with self.assertRaisesRegex(q.Error, "excluded"):
            q.check_plan(plan)

    def test_unrelated_crypto_capabilities_remain_valid(self):
        for description in ("Cryptocurrency token interoperability", "Stablecoin wallet and DeFi", "Post-quantum cryptography"):
            with self.subTest(description=description):
                manifest = self.manifest()
                manifest["repositories"][0]["description"] = description
                self.assertEqual(q.check_plan(q.make_plan(manifest)), q.validate(manifest))

    def test_checked_in_plan_matches_canonical_and_is_preview_only(self):
        plan = q.read_json(ROOT / "catalog/execution-plan.json")
        self.assertEqual(q.check_plan(plan), q.validate(q.read_json(ROOT / "catalog/canonical.json")))
        self.assertEqual(plan["mode"], "offline")
        self.assertTrue(all(a["action"] == "unverified" for a in plan["actions"]))


if __name__ == "__main__":
    unittest.main()

