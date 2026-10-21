#!/usr/bin/env python3
"""QMOOSA flagship and template-based repository initialization. Preview by default."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from urllib.parse import quote

WORK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("qmoosa_engine", WORK / "tools/qmoosa_engine.py")
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
HUB = "qmoosa-1000"
BRANCH = "qmoosa-scaffold"


def file_map(folder):
    folder = Path(folder)
    if folder.is_symlink():
        raise q.Error("Refusing to export a symlinked source directory.")
    ignored = {".git", ".local", ".venv", "venv", "__pycache__", "node_modules", "target",
               ".aws", ".ssh", ".gnupg", ".azure", ".config", ".idea", ".vscode"}
    result = {}
    for path in folder.rglob("*"):
        relative = path.relative_to(folder)
        if any(part in ignored for part in relative.parts):
            continue
        if path.is_symlink():
            raise q.Error("Refusing to export a symlink: " + relative.as_posix())
        if not path.is_file():
            continue
        name = path.name.lower()
        example = name.endswith((".example", ".sample", ".template"))
        if ((name == ".env" or name.startswith(".env.")) and not example
                or name in {".npmrc", ".pypirc", "credentials", "credentials.json", "service-account.json"}
                or path.suffix.lower() in {".pyc", ".pem", ".key", ".p12", ".pfx", ".keystore"}):
            continue
        result[relative.as_posix()] = path.read_text(encoding="utf-8-sig")
    return result


def head(api, prefix, branch):
    return api.call("GET", prefix+"/git/ref/heads/"+quote(branch,safe=""))["object"]["sha"]


def summary(state, plan):
    entries = state["repositories"]
    return dict(updated_at=q.stamp(), phase=state.get("phase","planning"),
                flagship="https://github.com/elon00/"+HUB+"/tree/main",
                target=len(plan["actions"]),
                existing_at_plan=sum(a["action"]=="skip" for a in plan["actions"]),
                generated=sum(e.get("created_response",False) for e in entries.values()),
                initialized=sum(e.get("status")=="verified" for e in entries.values()),
                additionally_observed=sum(e.get("status")=="existing" for e in entries.values()),
                incomplete=[n for n,e in entries.items() if e.get("status") not in ("verified","existing")],
                processed=len(entries), initial_missing=sum(a["action"]=="create" for a in plan["actions"]),
                implementation="not established", security_approval="not established",
                production_certification="not established", error=state.get("last_error"))


def wait_repo_ready(api, prefix, files, expected_id, private):
    for attempt in range(12):
        try:
            repo = api.call("GET",prefix)
            if repo["id"] != expected_id or repo["private"] != private or repo.get("fork"):
                raise q.Error("Repository identity, visibility, or fork status changed.")
            sha = head(api,prefix,repo["default_branch"])
            q.verify_tree(api,prefix,sha,files)
            return sha
        except q.ApiError as exc:
            if exc.status not in (404,409) or attempt == 11:
                raise
            time.sleep(5)
    raise q.Error("Repository was not ready for content verification.")


def ensure_hub(api, work, state, checkpoint):
    prefix = "/repos/elon00/"+HUB
    repo = q.remote_repo(api,prefix)
    h = state.setdefault("hub",{})
    if not h.get("repo_id"):
        if repo:
            raise q.Error("Flagship name already exists without this run's journal; refusing to modify it.")
        repo = api.call("POST","/user/repos",dict(name=HUB,private=True,auto_init=True,
                         description="QMOOSA-1000 flagship: canonical portfolio, references, and provisioning"))
        h["repo_id"] = repo["id"]
        checkpoint()
    if not repo or repo["id"] != h["repo_id"] or not repo["private"]:
        raise q.Error("Flagship identity or visibility mismatch.")
    if not h.get("main_ready"):
        if repo["default_branch"] != "main":
            existing_ref = None
            try:
                existing_ref = head(api,prefix,"main")
            except q.ApiError as exc:
                if exc.status != 404:
                    raise
            initial = head(api,prefix,repo["default_branch"])
            if existing_ref and existing_ref != initial:
                raise q.Error("Unexpected main branch on new flagship.")
            if not existing_ref:
                api.call("POST",prefix+"/git/refs",dict(ref="refs/heads/main",sha=initial))
            api.call("PATCH",prefix,dict(default_branch="main"))
        files = file_map(work)
        q.initialize(api,prefix,dict(private=True),h,files,checkpoint)
        h["main_commit"] = h["scaffold_commit"]
        h["main_ready"] = True
        checkpoint()
    template_files = file_map(work / "project-template")
    if not h.get("template_commit"):
        tree = api.call("POST",prefix+"/git/trees",dict(tree=[
            dict(path=p,mode="100644",type="blob",content=c) for p,c in sorted(template_files.items())]))
        commit = api.call("POST",prefix+"/git/commits",
                          dict(message="Create clean QMOOSA project template",tree=tree["sha"],parents=[]))
        h["template_commit"] = commit["sha"]
        checkpoint()
    try:
        current = head(api,prefix,BRANCH)
    except q.ApiError as exc:
        if exc.status != 404:
            raise
        api.call("POST",prefix+"/git/refs",dict(ref="refs/heads/"+BRANCH,sha=h["template_commit"]))
        current = h["template_commit"]
    if current != h["template_commit"]:
        raise q.Error("Template branch changed.")
    q.verify_tree(api,prefix,current,template_files)
    repo = api.call("GET",prefix)
    if not repo.get("is_template") or repo["default_branch"] != BRANCH:
        api.call("PATCH",prefix,dict(is_template=True,default_branch=BRANCH))
    h["ready"] = True
    checkpoint()


def publish_final(api, work, state, plan, checkpoint):
    prefix = "/repos/elon00/"+HUB
    h = state["hub"]
    if not state.get("finished_at"):
        state["finished_at"] = q.stamp()
        checkpoint()
    data = summary(state,plan)
    data["updated_at"] = state["finished_at"]
    data["phase"] = "initialization-complete"
    text = (work/"README.md").read_text(encoding="utf-8-sig")
    text += ("\n## Initialization result\n\n"
             f"Observed project repositories: {data['existing_at_plan']+data['initialized']+data['additionally_observed']} / {data['target']}.\n"
             f"New scaffolds verified in this run: {data['initialized']}.\n"
             "See execution-result.json for the recorded evidence. Product implementation and security certification remain unverified.\n")
    files = {"execution-result.json":json.dumps(data,indent=2)+"\n", "README.md":text}
    current = head(api,prefix,"main")
    candidate = h.get("final_commit")
    if current not in (h["main_commit"],candidate):
        raise q.Error("Flagship main advanced externally; refusing to overwrite.")
    if not candidate:
        base = api.call("GET",prefix+"/git/commits/"+current)
        tree = api.call("POST",prefix+"/git/trees",dict(base_tree=base["tree"]["sha"],
                tree=[dict(path=p,mode="100644",type="blob",content=c) for p,c in files.items()]))
        commit = api.call("POST",prefix+"/git/commits",dict(
            message="Record QMOOSA initialization results",tree=tree["sha"],parents=[current]))
        h["final_commit"] = commit["sha"]
        checkpoint()
    if current != h["final_commit"]:
        api.call("PATCH",prefix+"/git/refs/heads/main",dict(sha=h["final_commit"],force=False))
    q.verify_tree(api,prefix,h["final_commit"],files)
    api.call("PATCH",prefix,dict(default_branch="main",is_template=False))
    state["phase"] = "initialization-complete"
    checkpoint()


def run(api, work, limit):
    plan = q.read_json(work/"catalog/execution-plan.json")
    manifest = q.check_plan(plan)
    if manifest["owner"] != "elon00" or plan["mode"] != "live" or manifest["example"]:
        raise q.Error("Expected reviewed live elon00 execution plan.")
    if q.validate(q.read_json(work/"catalog/canonical.json")) != manifest:
        raise q.Error("Canonical manifest and reviewed plan differ.")
    if not 1 <= limit <= 1000:
        raise q.Error("limit must be from 1 to 1000.")
    inventory = q.inventory(api,"elon00")
    folder = work/".local"
    folder.mkdir(exist_ok=True)
    state_path = folder/"provisioning-state.json"
    identity = q.digest(dict(plan_id=plan["plan_id"],template=file_map(work/"project-template"),
                             worker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    with q.journal_lock(state_path):
        state = q.read_json(state_path) if state_path.exists() else dict(
            identity=identity,phase="starting",repositories={},created_at=q.stamp())
        if state["identity"] != identity:
            raise q.Error("State belongs to different code, template, or plan.")
        def checkpoint():
            q.save_json(state_path,state)
            q.save_json(folder/"progress.json",summary(state,plan))
        checkpoint()
        try:
            if state["phase"] == "initialization-complete":
                return summary(state,plan)
            state.pop("last_error",None)
            ensure_hub(api,work,state,checkpoint)
            state["phase"] = "initializing"
            checkpoint()
            files = file_map(work/"project-template")
            touched = 0
            for row,action in zip(manifest["repositories"],plan["actions"]):
                if action["action"] != "create":
                    continue
                name = row["name"]
                entry = state["repositories"].get(name)
                if entry and entry.get("status") in ("verified","existing"):
                    continue
                if touched >= limit:
                    break
                touched += 1
                prefix = "/repos/elon00/"+name
                repo = q.remote_repo(api,prefix)
                if entry and entry.get("repo_id"):
                    if not repo or repo["id"] != entry["repo_id"]:
                        raise q.Error("Journaled repository missing or ID changed: "+name)
                elif repo:
                    if entry and entry.get("status")=="attempting":
                        template = repo.get("template_repository") or {}
                        if template.get("id") != state["hub"]["repo_id"]:
                            raise q.Error("Uncertain generation has a different template: "+name)
                        wait_repo_ready(api,prefix,files,repo["id"],row["private"])
                        entry.update(repo_id=repo["id"],status="verified",reconciled_after_attempt=True,
                                     created_response=False,verified_at=q.stamp())
                    else:
                        state["repositories"][name] = dict(status="existing",observed_id=repo["id"])
                    checkpoint()
                    continue
                if not entry or not entry.get("repo_id"):
                    source_prefix = "/repos/elon00/"+HUB
                    source = api.call("GET",source_prefix)
                    if (source["id"] != state["hub"]["repo_id"] or not source["is_template"]
                            or source["default_branch"] != BRANCH
                            or head(api,source_prefix,BRANCH) != state["hub"]["template_commit"]):
                        raise q.Error("Template identity/default branch changed.")
                    entry = dict(status="attempting",attempted_at=q.stamp())
                    state["repositories"][name] = entry
                    checkpoint()
                    repo = api.call("POST",source_prefix+"/generate",dict(owner="elon00",name=name,
                            description=row["description"],private=row["private"],include_all_branches=False))
                    entry.update(repo_id=repo["id"],status="created",created_response=True,created_at=q.stamp())
                    checkpoint()
                sha = wait_repo_ready(api,prefix,files,entry["repo_id"],row["private"])
                entry.update(status="verified",head_sha=sha,verified_at=q.stamp())
                checkpoint()
                print(json.dumps(dict(name=name,**summary(state,plan))),flush=True)
            done = sum(e.get("status") in ("verified","existing") for e in state["repositories"].values())
            if done == sum(a["action"]=="create" for a in plan["actions"]):
                # Verify presence again, independently of the local journal, before finalizing.
                final_inventory = {r["name"].lower():r for r in q.inventory(api,"elon00")}
                if any(r["name"] not in final_inventory or final_inventory[r["name"]]["fork"]
                       for r in manifest["repositories"]):
                    raise q.Error("Final 1000-name inventory check failed.")
                publish_final(api,work,state,plan,checkpoint)
            else:
                state["phase"] = "batch-complete"
                checkpoint()
            return summary(state,plan)
        except Exception as exc:
            state["phase"] = "stopped"
            state["last_error"] = f"{type(exc).__name__}: {exc}"
            checkpoint()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--limit",type=int,default=10)
    args = parser.parse_args()
    plan = q.read_json(WORK/"catalog/execution-plan.json")
    q.check_plan(plan)
    if not args.execute:
        print(json.dumps(dict(**q.summarize(plan),flagship="elon00/"+HUB,
                              visibility="private",mode_note="Preview only; no network or writes"),indent=2))
        return
    print(json.dumps(run(q.GitHub(q.token()),WORK,args.limit),indent=2),flush=True)


if __name__ == "__main__":
    try:
        main()
    except (q.Error,OSError,ValueError,KeyError,TypeError) as exc:
        print("STOPPED: "+str(exc),file=sys.stderr,flush=True)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Stopped. Keep the journal to resume.",file=sys.stderr,flush=True)
        sys.exit(130)

