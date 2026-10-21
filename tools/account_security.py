#!/usr/bin/env python3
"""Check/enable free secret controls on owned public repositories; never publishes."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import threading

WORK = Path(__file__).resolve().parents[1]
STOP = threading.Event()
CONTROLS = ("secret_scanning", "secret_scanning_push_protection")


def api(endpoint, *, body=None, paginate=False):
    args = ["gh", "api", endpoint]
    if body is not None:
        args += ["--method", "PATCH", "--input", "-"]
    if paginate:
        args += ["--paginate", "--slurp"]
    result = subprocess.run(args, input=json.dumps(body) if body is not None else None,
                            capture_output=True, text=True, encoding="utf-8", timeout=300)
    if result.returncode:
        if any(part in result.stderr for part in ("rate limit", "HTTP 401")):
            STOP.set()
        raise RuntimeError(result.stderr[:700])
    return json.loads(result.stdout)


def statuses(metadata):
    settings = metadata.get("security_and_analysis") or {}
    return {control: settings.get(control, {}).get("status", "unknown") for control in CONTROLS}


def harden(repo, owner, apply):
    full = repo["full_name"]
    if STOP.is_set():
        return {"repository": full, "status": "retry_after_api_limit_or_auth_fix"}
    if full.lower() != owner.lower() + "/" + repo["name"].lower() or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo["name"]):
        raise RuntimeError("Repository identity mismatch")
    try:
        current = api("repos/" + full)
        if current["id"] != repo["id"] or current["owner"]["login"].lower() != owner.lower():
            raise RuntimeError("Repository owner or identity changed")
        if current["private"]:
            return {"repository": full, "status": "private_held", "changed": False}
        if not current.get("permissions", {}).get("admin"):
            raise RuntimeError("Repository admin access required")
        previous = statuses(current)
        changed = False
        if any(value != "enabled" for value in previous.values()):
            if not apply:
                return {"repository": full, "status": "needs_changes", "previous": previous, "changed": False}
            current = api("repos/" + full, body={"security_and_analysis": {
                control: {"status": "enabled"} for control in CONTROLS}})
            changed = True
        final = statuses(current)
        if current["private"] or current["id"] != repo["id"] or any(value != "enabled" for value in final.values()):
            raise RuntimeError("Security settings verification failed")
        return {"repository": full, "status": "protected", "changed": changed, "previous": previous, "current": final}
    except Exception as error:
        message = str(error)
        return {"repository": full, "status": "inaccessible" if "HTTP 451" in message else "requires_review", "error": message[:700]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--workers", type=int, choices=(1, 2, 4), default=4)
    args = parser.parse_args()
    authenticated = api("user")["login"]
    if authenticated.lower() != args.owner.lower():
        raise RuntimeError("Authenticate as the requested account owner first")
    pages = api("/user/repos?affiliation=owner&visibility=all&per_page=100&sort=full_name", paginate=True)
    repos = [repo for page in pages for repo in page]
    if any(repo["owner"]["login"].lower() != args.owner.lower() for repo in repos):
        raise RuntimeError("Unexpected owner in the authenticated repository listing")
    destination = WORK / ".local/account-security.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    results = []
    print(f"Checking {len(repos)} owned repositories; apply={args.apply}; private repositories remain unchanged", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        tasks = [pool.submit(harden, repo, args.owner, args.apply) for repo in repos]
        for task in as_completed(tasks):
            results.append(task.result())
            report = {"updated_at": datetime.now(timezone.utc).isoformat(), "owner": args.owner,
                      "expected": len(repos), "complete": len(results) == len(repos),
                      "counts": dict(Counter(item["status"] for item in results)), "repositories": results}
            temporary = destination.with_suffix(".tmp")
            temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            temporary.replace(destination)
            if len(results) % 25 == 0 or len(results) == len(repos):
                print(f"Checked {len(results)}/{len(repos)}: {report['counts']}", flush=True)
    return 1 if any(item["status"] != "protected" for item in results) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print("BLOCKED: " + str(error))
        raise SystemExit(2)
