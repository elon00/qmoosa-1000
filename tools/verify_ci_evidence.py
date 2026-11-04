#!/usr/bin/env python3
"""Conservative, offline QMOOSA-1000 GitHub evidence reconciliation.

This tool does not fetch GitHub data, trigger CI, or certify implementations.
Supply independently captured repository metadata, default-branch HEADs,
workflow runs and workflow jobs. Missing evidence always fails closed.
"""
import argparse
from collections import Counter
import json
import re
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")


def verified_run(repo):
    """Return one evidence run ID, or None when exact default-HEAD proof is absent."""
    branch = repo.get("default_branch")
    sha = repo.get("default_head_sha")
    if not isinstance(branch, str) or not branch or not isinstance(sha, str) or not SHA40.fullmatch(sha):
        return None
    runs = repo.get("workflow_runs")
    if not isinstance(runs, list):
        return None
    for run in runs:
        if not isinstance(run, dict):
            continue
        if (run.get("head_branch") != branch or run.get("head_sha") != sha
                or run.get("status") != "completed" or run.get("conclusion") != "success"):
            continue
        jobs = run.get("jobs")
        if not isinstance(jobs, list) or not jobs:
            continue
        if any(not isinstance(job, dict) or job.get("status") != "completed"
               or job.get("conclusion") != "success" for job in jobs):
            continue
        run_id = run.get("id")
        if isinstance(run_id, int) and not isinstance(run_id, bool) and run_id > 0:
            return run_id
    return None


def reconcile(manifest, evidence):
    owner = manifest.get("owner")
    approved = manifest.get("repositories")
    if not isinstance(owner, str) or not owner or not isinstance(approved, list):
        raise ValueError("Manifest must contain owner and repositories")
    names = [item.get("name") for item in approved if isinstance(item, dict)]
    if len(names) != len(approved) or any(not isinstance(n, str) or not n for n in names):
        raise ValueError("Invalid approved repository names")
    if len(set(names)) != len(names):
        raise ValueError("Duplicate approved names")
    if manifest.get("target_total") != len(names):
        raise ValueError("Manifest target_total does not match unique approved names")
    snapshots = evidence.get("repositories")
    if not isinstance(snapshots, list):
        raise ValueError("Evidence must contain repositories array")
    by_name = {}
    rejected = []
    name_counts = Counter(r.get("name") for r in snapshots if isinstance(r, dict) and isinstance(r.get("name"), str))
    id_counts = Counter(r.get("id") for r in snapshots if isinstance(r, dict)
                        and isinstance(r.get("id"), int) and not isinstance(r.get("id"), bool))
    for repo in snapshots:
        if not isinstance(repo, dict):
            rejected.append("malformed repository evidence")
            continue
        full = repo.get("repository_full_name")
        repo_id = repo.get("id")
        name = repo.get("name")
        if (name not in names or full != f"{owner}/{name}"
                or repo.get("fork") is not False
                or not isinstance(repo_id, int) or isinstance(repo_id, bool) or repo_id <= 0
                or name_counts[name] != 1 or id_counts[repo_id] != 1):
            rejected.append(str(full or name or "unknown"))
            continue
        by_name[name] = repo
    verified = {name: verified_run(repo) for name, repo in by_name.items()}
    return {
        "target": len(names),
        "created_exact_nonfork": len(by_name),
        "ci_verified_current_default_head": sum(run is not None for run in verified.values()),
        "ci_evidence_run_ids": {name: run for name, run in verified.items() if run is not None},
        "implementation_verified": None,
        "security_approved": None,
        "deployment_ready": None,
        "production_certified": None,
        "missing_or_unverified_names": sorted(set(names) - set(by_name)),
        "rejected_evidence": rejected,
        "warning": "Snapshot-only: counts depend on evidence completeness and freshness; CI does not prove implementation or security acceptance."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = reconcile(json.loads(args.manifest.read_text(encoding="utf-8")),
                       json.loads(args.evidence.read_text(encoding="utf-8")))
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
