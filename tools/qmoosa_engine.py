#!/usr/bin/env python3
"""Manifest-driven GitHub scaffolding. Python standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler

API = "https://api.github.com"
API_VERSION = "2026-03-10"
MAX_REPOS = 1000


class Error(Exception):
    pass


class ApiError(Error):
    def __init__(self, status, headers=None):
        self.status = status
        headers = headers or {}
        detail = ""
        if status in (403, 429):
            detail = (" Stop and inspect permissions/rate limits. Retry-After="
                      + str(headers.get("Retry-After", "unspecified"))
                      + "; reset=" + str(headers.get("X-RateLimit-Reset", "unspecified")))
        super().__init__(f"GitHub HTTP {status}.{detail} No automatic write retry.")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate(raw):
    if not isinstance(raw, dict):
        raise Error("Manifest must be a JSON object.")
    allowed = {"schema_version", "example", "owner", "target_total", "repositories"}
    if set(raw) - allowed:
        raise Error("Unknown manifest fields; explicitly convert the source schema first.")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise Error("schema_version must be 1.")
    owner = raw.get("owner")
    if (not isinstance(owner, str) or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner)
            or "--" in owner):
        raise Error("Invalid personal GitHub owner.")
    total = raw.get("target_total")
    if type(total) is not int or not 1 <= total <= MAX_REPOS:
        raise Error("target_total must be an integer from 1 to 1000.")
    rows = raw.get("repositories")
    if not isinstance(rows, list) or len(rows) != total:
        raise Error("repositories must contain exactly target_total names, including existing projects.")
    if type(raw.get("example", False)) is not bool:
        raise Error("example must be a boolean.")
    result = []
    names = set()
    reserved = {"con", "prn", "aux", "nul"} | {f"{a}{n}" for a in ("com", "lpt") for n in range(1, 10)}
    for row in rows:
        if not isinstance(row, dict) or set(row) - {"name", "description", "template", "private"}:
            raise Error("Invalid repository entry or unknown field.")
        name = row.get("name")
        if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,99}", name)
                or name.endswith(".") or name.split(".")[0] in reserved):
            raise Error("Repository names must be lowercase, filesystem-safe, and at most 100 characters.")
        if name in names:
            raise Error(f"Duplicate repository name: {name}")
        names.add(name)
        template = row.get("template", "basic")
        if template not in ("basic", "python", "node"):
            raise Error(f"Unknown template for {name}.")
        private = row.get("private", True)
        description = row.get("description", "")
        if type(private) is not bool or not isinstance(description, str) or len(description) > 350:
            raise Error(f"Invalid visibility or description for {name}.")
        if any(ord(ch) < 32 for ch in description):
            raise Error(f"Control characters are not allowed in description for {name}.")
        result.append(dict(name=name, description=description, template=template, private=private))
    return dict(schema_version=1, example=raw.get("example", False), owner=owner.lower(),
                target_total=total, repositories=result)


def scaffold(row, manifest_hash):
    name = row["name"]
    files = {
        "README.md": f"# {name}\n\n{row['description'] or 'Project structure awaiting implementation.'}\n\n"
                     "Status: scaffold only.\n\n"
                     "- Implementation: not verified\n- CI: not evaluated\n"
                     "- Security approval: not verified\n- Deployment readiness: not verified\n"
                     "- Production certification: not verified\n\n"
                     "Add requirements, implementation, and real tests before making readiness claims.\n",
        ".gitignore": ".env\n.env.*\n!.env.example\n__pycache__/\n*.pyc\n.venv/\nnode_modules/\ndist/\n",
        "docs/README.md": "# Documentation\n\nDefine requirements, architecture, and acceptance criteria here.\n",
        "tests/README.md": "# Tests\n\nAdd meaningful tests for implemented behavior. No product tests exist yet.\n",
        ".qmoosa/scaffold.json": json.dumps(dict(generator="qmoosa-github-initializer/1.0.0",
                                                manifest_sha256=manifest_hash, name=name,
                                                status="scaffold-only"), sort_keys=True, indent=2) + "\n",
    }
    if row["template"] == "python":
        module = re.sub(r"[^a-z0-9_]", "_", name)
        if module[0].isdigit():
            module = "project_" + module
        files["pyproject.toml"] = (f'[project]\nname = "{name}"\nversion = "0.0.0"\n'
                                  'description = "Scaffold awaiting implementation"\nrequires-python = ">=3.10"\n')
        files[f"src/{module}/__init__.py"] = '"""Project scaffold. Implementation is pending."""\n'
    elif row["template"] == "node":
        files["package.json"] = json.dumps(dict(name=re.sub(r"[^a-z0-9-]", "-", name),
                                                version="0.0.0", private=True,
                                                description="Scaffold awaiting implementation",
                                                type="module"), indent=2) + "\n"
        files["src/index.js"] = "// Project scaffold. Implementation is pending.\n"
    else:
        files["src/README.md"] = "# Source\n\nImplement the project here after requirements are approved.\n"
    return files


def token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    try:
        result = subprocess.run(["gh", "auth", "token", "--hostname", "github.com"],
                                capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    raise Error("Authenticate with gh auth login or set GH_TOKEN. Never put tokens in a manifest.")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    def __init__(self, credential=None, interval=10):
        self.credential = credential
        self.interval = max(10, interval)
        self.last_write = time.monotonic()  # Space writes even across fresh batch invocations.
        self.opener = build_opener(NoRedirect())

    def call(self, method, path, body=None):
        if not path.startswith("/") or path.startswith("//"):
            raise Error("Invalid API path.")
        if method != "GET":
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_write)))
            self.last_write = time.monotonic()
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
                   "User-Agent": "qmoosa-github-initializer/1.0.0"}
        if self.credential:
            headers["Authorization"] = "Bearer " + self.credential
        data = None if body is None else canonical(body)
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            with self.opener.open(Request(API + path, data=data, headers=headers, method=method),
                                  timeout=45) as response:
                return json.load(response)
        except HTTPError as exc:
            raise ApiError(exc.code, exc.headers) from None
        except (URLError, TimeoutError, OSError) as exc:
            detail = ("Read failed; remote data was not verified." if method == "GET" else
                      "Write outcome may be unknown; inspect the journal and remote before resuming.")
            raise Error(f"GitHub transport error ({type(exc).__name__}). {detail}") from None


def inventory(api, owner, public=False):
    if not public:
        user = api.call("GET", "/user")
        if user["login"].lower() != owner.lower():
            raise Error(f"Authenticated owner is {user['login']}; expected {owner}.")
    rows = []
    page = 1
    while True:
        prefix = f"/users/{owner}/repos?type=owner&" if public else "/user/repos?affiliation=owner&"
        batch = api.call("GET", prefix + f"per_page=100&page={page}&sort=full_name")
        if not isinstance(batch, list):
            raise Error("Unexpected inventory response.")
        rows.extend(dict(name=r["name"], id=r["id"], private=r["private"], fork=r["fork"])
                    for r in batch if r["owner"]["login"].lower() == owner.lower())
        if len(batch) < 100:
            break
        page += 1
    return sorted(rows, key=lambda r: r["name"].lower())


def engine_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def make_plan(manifest, current=None):
    manifest = validate(manifest)
    offline = current is None
    existing = {r["name"].lower(): r for r in (current or [])}
    actions = []
    for row in manifest["repositories"]:
        old = existing.get(row["name"])
        actions.append(dict(name=row["name"], action="unverified" if offline else "skip" if old else "create",
                            existing_id=old["id"] if old else None,
                            scaffold_sha256=digest(scaffold(row, digest(manifest)))))
    result = dict(schema_version=1, created_at=stamp(), mode="offline" if offline else "live",
                  engine_sha256=engine_hash(), manifest=manifest, manifest_sha256=digest(manifest),
                  inventory=current, actions=actions)
    result["plan_id"] = digest(result)
    return result


def check_plan(plan):
    unsigned = {k: v for k, v in plan.items() if k != "plan_id"}
    if plan.get("plan_id") != digest(unsigned):
        raise Error("Plan checksum mismatch; create a new plan.")
    if plan.get("engine_sha256") != engine_hash():
        raise Error("Plugin code changed since planning; create a new plan.")
    manifest = validate(plan["manifest"])
    expected = make_plan(manifest, plan["inventory"])
    if (plan["actions"] != expected["actions"] or plan["mode"] != expected["mode"]
            or plan["manifest_sha256"] != digest(manifest)):
        raise Error("Plan contents do not match the manifest and inventory.")
    return manifest


def summarize(plan):
    actions = plan["actions"]
    return dict(owner=plan["manifest"]["owner"], target_total=len(actions),
                existing=sum(a["action"] == "skip" for a in actions),
                to_create=sum(a["action"] == "create" for a in actions),
                unverified=sum(a["action"] == "unverified" for a in actions),
                public_requested=sum(not r["private"] for r in plan["manifest"]["repositories"]),
                plan_id=plan["plan_id"], mode=plan["mode"])


def remote_repo(api, prefix):
    try:
        return api.call("GET", prefix)
    except ApiError as exc:
        if exc.status == 404:
            return None
        raise


def git_blob(content):
    raw = content.encode()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def verify_tree(api, prefix, sha, files):
    commit = api.call("GET", prefix + f"/git/commits/{sha}")
    tree_sha = commit["tree"]["sha"]
    tree = api.call("GET", prefix + f"/git/trees/{tree_sha}?recursive=1")
    if tree.get("truncated"):
        raise Error("Remote tree is truncated; cannot verify scaffold.")
    actual = {r["path"]: r["sha"] for r in tree["tree"] if r["type"] == "blob"}
    if any(actual.get(path) != git_blob(content) for path, content in files.items()):
        raise Error("Remote scaffold content verification failed.")


@contextmanager
def journal_lock(path):
    lock = Path(str(path) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Error("State is locked. If a process crashed, check it has stopped before removing the .lock file.")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def initialize(api, prefix, row, entry, files, checkpoint):
    repo = api.call("GET", prefix)
    if repo["id"] != entry["repo_id"] or repo["private"] != row["private"] or repo.get("fork"):
        raise Error("Repository ID, visibility, or fork status changed; stopping.")
    branch = repo["default_branch"]
    if entry.get("branch") and entry["branch"] != branch:
        raise Error("Default branch changed; stopping.")
    entry["branch"] = branch
    ref_path = prefix + "/git/refs/heads/" + quote(branch, safe="")
    head = api.call("GET", prefix + "/git/ref/heads/" + quote(branch, safe=""))["object"]["sha"]
    files_hash = digest(files)
    if entry.get("files_sha256") and entry["files_sha256"] != files_hash:
        raise Error("Scaffold changed; stopping.")
    entry["files_sha256"] = files_hash
    if not entry.get("base_sha"):
        initial = api.call("GET", prefix + "/git/commits/" + head)
        tree = api.call("GET", prefix + "/git/trees/" + initial["tree"]["sha"] + "?recursive=1")
        if (initial.get("parents") or tree.get("truncated") or
                {r["path"] for r in tree["tree"]} != {"README.md"}):
            raise Error("New repository changed before scaffolding; stopping for reconciliation.")
        entry["base_sha"] = head
        checkpoint()
    candidate = entry.get("scaffold_commit")
    if candidate and head == candidate:
        verify_tree(api, prefix, head, files)
        entry.update(status="complete", verified_at=stamp())
        checkpoint()
        return
    if head != entry["base_sha"]:
        raise Error("Branch advanced after initialization began; refusing to overwrite.")
    if not candidate:
        base = api.call("GET", prefix + "/git/commits/" + head)
        tree = api.call("POST", prefix + "/git/trees",
                        dict(base_tree=base["tree"]["sha"],
                             tree=[dict(path=path, mode="100644", type="blob", content=content)
                                   for path, content in sorted(files.items())]))
        commit = api.call("POST", prefix + "/git/commits",
                         dict(message="Initialize basic project scaffold", tree=tree["sha"], parents=[head]))
        entry["scaffold_commit"] = commit["sha"]
        checkpoint()
    api.call("PATCH", ref_path, dict(sha=entry["scaffold_commit"], force=False))
    head = api.call("GET", prefix + "/git/ref/heads/" + quote(branch, safe=""))["object"]["sha"]
    if head != entry["scaffold_commit"]:
        raise Error("Branch moved before verification; stopping.")
    verify_tree(api, prefix, head, files)
    entry.update(status="complete", verified_at=stamp())
    checkpoint()


def apply_plan(plan, state_path, api, confirm_owner, limit=10):
    manifest = check_plan(plan)
    if plan["mode"] != "live" or manifest["example"]:
        raise Error("Only a live plan from a non-example manifest can be applied.")
    if confirm_owner.lower() != manifest["owner"]:
        raise Error("--confirm-owner does not match the manifest.")
    if type(limit) is not int or not 1 <= limit <= MAX_REPOS:
        raise Error("--limit must be from 1 to 1000.")
    # Recheck authentication and current inventory before any mutation.
    inventory(api, manifest["owner"])
    state_path = Path(state_path)
    with journal_lock(state_path):
        state = read_json(state_path) if state_path.exists() else dict(plan_id=plan["plan_id"], repositories={})
        if state.get("plan_id") != plan["plan_id"] or not isinstance(state.get("repositories"), dict):
            raise Error("State belongs to another plan or is invalid.")
        checkpoint = lambda: save_json(state_path, state)
        checkpoint()  # Test durable journal storage before the first remote write.
        touched = 0
        for action, row in zip(plan["actions"], manifest["repositories"]):
            if action["action"] != "create":
                continue
            name = row["name"]
            prefix = f"/repos/{manifest['owner']}/{name}"
            entry = state["repositories"].get(name)
            repo = remote_repo(api, prefix)
            if entry and "repo_id" in entry:
                if not repo or repo["id"] != entry["repo_id"]:
                    raise Error("A journaled repository is missing or has a different ID.")
                if entry["status"] == "complete":
                    files = scaffold(row, plan["manifest_sha256"])
                    initialize(api, prefix, row, entry, files, checkpoint)
                    continue
            elif repo:
                state["repositories"][name] = dict(status="skipped-existing", observed_id=repo["id"])
                checkpoint()
                continue
            if touched >= limit:
                break
            touched += 1
            if not entry or "repo_id" not in entry:
                # A POST is never retried automatically. A lost response requires manual reconciliation.
                repo = api.call("POST", "/user/repos", dict(name=name, description=row["description"],
                                                           private=row["private"], auto_init=True))
                entry = dict(repo_id=repo["id"], status="created", created_at=stamp())
                state["repositories"][name] = entry
                checkpoint()
            initialize(api, prefix, row, entry, scaffold(row, plan["manifest_sha256"]), checkpoint)
        return dict(plan_id=plan["plan_id"],
                    created_by_this_plan=sum("repo_id" in e for e in state["repositories"].values()),
                    scaffolds_verified=sum(e["status"] == "complete" for e in state["repositories"].values()),
                    skipped_existing=sum(e["status"] == "skipped-existing" for e in state["repositories"].values()),
                    incomplete=sum("repo_id" in e and e["status"] != "complete"
                                   for e in state["repositories"].values()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--manifest", required=True)
    i = sub.add_parser("inventory")
    i.add_argument("--owner", required=True)
    i.add_argument("--public", action="store_true")
    i.add_argument("--output", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--offline", action="store_true")
    r = sub.add_parser("render")
    r.add_argument("--plan", required=True)
    r.add_argument("--out", required=True)
    a = sub.add_parser("apply")
    a.add_argument("--plan", required=True)
    a.add_argument("--state", required=True)
    a.add_argument("--confirm-owner", required=True)
    a.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    if args.command == "validate":
        manifest = validate(read_json(args.manifest))
        result = dict(owner=manifest["owner"], count=manifest["target_total"],
                      manifest_sha256=digest(manifest), example=manifest["example"])
    elif args.command == "inventory":
        if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", args.owner):
            raise Error("Invalid owner.")
        api = GitHub(None if args.public else token())
        rows = inventory(api, args.owner, args.public)
        snapshot = dict(owner=args.owner, observed_at=stamp(),
                        scope="public-only" if args.public else "credential-visible-owned",
                        repositories=rows)
        save_json(args.output, snapshot)
        result = dict(owner=args.owner, count=len(rows), scope=snapshot["scope"])
    elif args.command == "plan":
        manifest = validate(read_json(args.manifest))
        if manifest["example"] and not args.offline:
            raise Error("Example manifests are for offline previews only.")
        rows = None if args.offline else inventory(GitHub(token()), manifest["owner"])
        plan = make_plan(manifest, rows)
        if Path(args.output).exists():
            raise Error("Plan output already exists; choose a new path to preserve resumability.")
        save_json(args.output, plan)
        result = summarize(plan)
    elif args.command == "render":
        plan = read_json(args.plan)
        manifest = check_plan(plan)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=False)
        for row in manifest["repositories"]:
            for relative, content in scaffold(row, plan["manifest_sha256"]).items():
                path = out / row["name"] / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
        result = dict(rendered=len(manifest["repositories"]), output=str(out.resolve()))
    else:
        plan = read_json(args.plan)
        # Reject invalid/offline plans before reading credentials.
        manifest = check_plan(plan)
        if plan["mode"] != "live" or manifest["example"]:
            raise Error("Offline and example plans cannot be applied.")
        result = apply_plan(plan, args.state, GitHub(token()), args.confirm_owner, args.limit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Stopped. Preserve the plan and state files to resume.", file=sys.stderr)
        sys.exit(130)

