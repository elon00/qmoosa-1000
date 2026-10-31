#!/usr/bin/env python3
"""Offline, fail-closed reconciliation of approved QMOOSA names and GitHub owner inventory.

No network, credentials, repository writes, or CI/production certification.
"""
import argparse
import json
from pathlib import Path
import sys

OWNER = "elon00"


class InventoryError(ValueError):
    pass


def approved_names(manifest):
    if (not isinstance(manifest, dict) or manifest.get("owner") != OWNER
            or manifest.get("target_total") != 1000
            or not isinstance(manifest.get("repositories"), list)):
        raise InventoryError("Expected canonical v3 owner manifest with 1000 repositories")
    names = []
    for row in manifest["repositories"]:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"]:
            raise InventoryError("Invalid canonical name")
        names.append(row["name"])
    if len(names) != 1000 or len(set(names)) != 1000:
        raise InventoryError("Canonical manifest must have exactly 1000 unique names")
    return set(names)


def load_inventory(text):
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        try:
            parsed = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError as exc:
            raise InventoryError("Inventory must be JSON or JSON lines") from exc
    if not isinstance(parsed, list):
        raise InventoryError("Inventory must be a JSON array or JSON lines")
    rows = []
    for page in parsed:
        if isinstance(page, list):
            rows.extend(page)
        else:
            rows.append(page)
    return rows


def reconcile(manifest, inventory):
    canonical = approved_names(manifest)
    ids = {}
    names = {}
    skipped_forks = 0
    skipped_other_owners = 0
    for row in inventory:
        if not isinstance(row, dict):
            raise InventoryError("Non-object inventory entry")
        owner = row.get("owner")
        login = owner.get("login") if isinstance(owner, dict) else None
        if not isinstance(login, str):
            raise InventoryError("Missing authoritative owner.login")
        if login.casefold() != OWNER:
            skipped_other_owners += 1
            continue
        if type(row.get("fork")) is not bool:
            raise InventoryError("Missing authoritative fork boolean")
        if row["fork"]:
            skipped_forks += 1
            continue
        name, rid = row.get("name"), row.get("id")
        if not isinstance(name, str) or not name or type(rid) is not int or rid <= 0:
            raise InventoryError("Invalid repository name or stable numeric ID")
        full_name = row.get("full_name")
        if not isinstance(full_name, str) or full_name.casefold() != (OWNER + "/" + name).casefold():
            raise InventoryError("Owner/name mismatch for " + name)
        if rid in ids and ids[rid] != name:
            raise InventoryError("Stable repository ID maps to multiple names")
        if name in names and names[name] != rid:
            raise InventoryError("Repository name maps to multiple stable IDs")
        ids[rid] = name
        names[name] = rid
    exact = sorted(canonical.intersection(names))
    missing = sorted(canonical.difference(names))
    unrelated = sorted(set(names).difference(canonical))
    return {
        "owner": OWNER,
        "manifest_unique": 1000,
        "inventory_complete": False,
        "inventory_scope": "observed_records_only; not proof of exhaustive owner pagination",
        "created_exact_observed_lower_bound": len(exact),
        "exact_matches": [{"name": name, "repository_id": names[name]} for name in exact],
        "unmatched_manifest_names_not_proven_missing": missing,
        "other_owned_original_repos_excluded": unrelated,
        "observed_unique_owned_original_repos": len(names),
        "excluded_fork_records": skipped_forks,
        "excluded_other_owner_records": skipped_other_owners,
        "implemented": "not_verified",
        "current_head_ci_verified": "not_verified",
        "security_approved": "not_verified",
        "deployment_ready": "not_verified",
        "production_certified": "not_verified",
        "manifest_completion_flags_are_not_evidence": True,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", default="catalog/canonical.json")
    p.add_argument("--inventory", required=True, help="JSON from gh api --paginate --slurp, or JSONL")
    p.add_argument("--output", help="Optional local JSON checkpoint path")
    args = p.parse_args(argv)
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        inventory = load_inventory(Path(args.inventory).read_text(encoding="utf-8-sig"))
        report = reconcile(manifest, inventory)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"RECONCILIATION FAILED: {exc}", file=sys.stderr)
        return 2
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CREATED observed exact: {report['created_exact_observed_lower_bound']}/1000; "
          f"owner originals observed: {report['observed_unique_owned_original_repos']}; "
          "inventory exhaustive: NO; CI/security/deployment: NOT VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
