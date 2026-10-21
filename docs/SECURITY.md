# Keeping credentials out of public projects

Use environment variables or the deployment platform's secret store for real credentials. Keep production `.env` files, wallet keystores and signing keys outside Git. For GitHub Actions, use repository/environment **Secrets**, not ordinary Variables. Browser bundles expose `VITE_*` and `NEXT_PUBLIC_*` values: a private service credential belongs on a backend.

The ignored `.local/` directory contains scanner binaries and redacted reports. The guard verifies official Gitleaks 8.30.1 archive checksums at installation and rechecks the executable against that archive before execution. It supports Windows x64 and Linux x64, and uses Python's standard library.

```text
python tools/security_guard.py install
python tools/security_guard.py scan --repo path/to/project
```

Run the scan before committing. It checks complete available local Git history and staged changes, rejects shallow history and changing refs/index content, and ignores repository-controlled scanner suppression files/comments. Known harmless tests require exact path, rule, line and file-content hashes. Reports contain finding locations and rule identifiers, with no matched credential values. Exit codes: 0 passed, 1 findings, 2 incomplete/error. A passing scan is a point-in-time automated check.

This command does not publish repositories and does not assess hosted logs, issues, releases, wiki pages or arbitrary confidential customer data. Those require the separate publication review. GitHub secret scanning and push protection provide an additional server-side control; retain them for public repositories. Keep build and deployment credentials scoped separately.

`.gitignore` cannot erase existing commits or revoke a credential. If a real credential is exposed, revoke/rotate it through its provider first. History cleanup needs coordination; do not force-push a blanket rewrite. Follow [GitHub's sensitive-data removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). Never paste tokens, wallet keys or recovery phrases into issues or chat.

## Check account controls

With GitHub CLI authenticated as the account owner, inspect the public repository controls:

```text
python tools/account_security.py --owner elon00
```

Add `--apply` to enable GitHub secret scanning and push protection on owned public repositories. This command never changes visibility, creates repositories, or enables paid private-repository features. Private repositories and inaccessible repositories require separate review. Progress and sanitized settings are saved in `.local/account-security.json`; no credential values are collected. This checks settings, not the absence of secrets or unresolved GitHub alerts.

The historical provisioning tool now excludes Git metadata, local state, credential files and key material from its export walk and rejects symlinks. Its old private/scaffold catalogs describe the original creation plan; do not rerun provisioning to harden existing products.
