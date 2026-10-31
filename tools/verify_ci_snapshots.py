#!/usr/bin/env python3
"""Offline CI evidence classifier; snapshots are NOT authenticated by this script.

Input: a JSON list of {repository, branch, runs, required_workflows} objects.
Each object should contain unmodified GitHub REST API response objects. The
caller must independently establish source provenance, pagination and current
HEAD freshness before treating any matching result as CI_VERIFIED.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")


class SnapshotError(ValueError):
    pass


def classify(snapshot, approved_names):
    if not isinstance(snapshot, dict):
        raise SnapshotError("Snapshot must be an object")
    repo = snapshot.get("repository")
    branch = snapshot.get("branch")
    runs = snapshot.get("runs")
    required = snapshot.get("required_workflows")
    if not isinstance(repo, dict) or not isinstance(branch, dict):
        raise SnapshotError("Missing repository or branch response")
    if not isinstance(runs, dict) or not isinstance(runs.get("workflow_runs"), list):
        raise SnapshotError("Missing GitHub workflow_runs response")
    if not isinstance(required, list) or not required or any(not isinstance(x, str) or not x for x in required):
        raise SnapshotError("Specify at least one required workflow name")
    if len(set(required)) != len(required):
        raise SnapshotError("Duplicate required workflow")
    owner = repo.get("owner")
    name = repo.get("name")
    rid = repo.get("id")
    if (not isinstance(owner, dict) or not isinstance(owner.get("login"), str)
            or owner["login"].casefold() != "elon00"
            or repo.get("fork") is not False or not isinstance(name, str)
            or not name or type(rid) is not int or rid <= 0
            or repo.get("full_name", "").casefold() != ("elon00/" + name).casefold()):
        raise SnapshotError("Repository owner, fork status, identity or ID invalid")
    if name not in approved_names:
        raise SnapshotError("Repository not in canonical approved manifest")
    default = repo.get("default_branch")
    head = (branch.get("commit") or {}).get("sha")
    if not isinstance(default, str) or not default or not isinstance(head, str) or not SHA40.fullmatch(head):
        raise SnapshotError("Invalid default branch or full commit SHA")
    if branch.get("name") != default:
        raise SnapshotError("Branch response is not the repository default branch")
    reasons = []
    matching = []
    for workflow in required:
        candidates = [r for r in runs["workflow_runs"] if isinstance(r, dict)
                      and r.get("name") == workflow and r.get("head_sha") == head
                      and r.get("head_branch") == default and r.get("event") == "push"]
        if not candidates:
            reasons.append(f"No push-triggered current-HEAD run for {workflow}")
            continue
        for r in candidates:
            if type(r.get("id")) is not int or r["id"] <= 0:
                raise SnapshotError("Invalid workflow run ID")
        latest = max(candidates, key=lambda r: (r["id"], r.get("run_attempt", 1)))
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            reasons.append(f"Latest current-HEAD run for {workflow} is not SUCCESS")
        else:
            matching.append({"workflow": workflow, "run_id": latest["id"]})
    return {
        "repository": "elon00/" + name,
        "repository_id": rid,
        "default_branch": default,
        "head_sha": head,
        "snapshot_ci_match": not reasons,
        "required_workflows": required,
        "matched_successful_runs": matching,
        "blockers": reasons,
        "independently_authenticated": False,
        "inventory_complete": False,
        "security_approved": False,
        "deployment_ready": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", required=True)
    parser.add_argument("--manifest", default="catalog/canonical.json")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        if (not isinstance(manifest, dict) or manifest.get("owner") != "elon00"
                or manifest.get("target_total") != 1000 or not isinstance(manifest.get("repositories"), list)):
            raise SnapshotError("Invalid canonical manifest")
        approved = [x.get("name") for x in manifest["repositories"] if isinstance(x, dict)]
        if (len(approved) != 1000 or any(not isinstance(x, str) or not x for x in approved)
                or len(set(approved)) != 1000):
            raise SnapshotError("Expected exactly 1000 unique approved names")
        snapshots = json.loads(Path(args.snapshots).read_text(encoding="utf-8-sig"))
        if not isinstance(snapshots, list):
            raise SnapshotError("Snapshots must be a JSON array")
        results = [classify(s, set(approved)) for s in snapshots]
        names = [r["repository"].casefold() for r in results]
        ids = [r["repository_id"] for r in results]
        if len(names) != len(set(names)) or len(ids) != len(set(ids)):
            raise SnapshotError("Duplicate repository name or stable ID")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"CI SNAPSHOT REJECTED: {exc}", file=sys.stderr)
        return 2
    report = {"source": "untrusted_offline_snapshots", "results": results,
              "matched_snapshot_count": sum(x["snapshot_ci_match"] for x in results),
              "portfolio_ci_verified": "not_established"}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Matched {report['matched_snapshot_count']}/{len(results)} offline snapshots; "
          "authenticated portfolio CI verification: NOT ESTABLISHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
