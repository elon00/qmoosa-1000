# QMOOSA-1000 Flagship

Portfolio hub for the canonical project catalog and reusable credential safeguards. The account-wide hardening mission inventories 1,823 owned repositories; the catalog below retains the original 1,000-project plan.

The working flagship demo is [Plonky](https://elon00.github.io/plonky/). Its [verified shared release](https://github.com/elon00/plonky/tree/7d65b4a5a98b2095ab638b780e445e6917ba05a1) was built and self-checked in 925 repositories. These share one implementation; separate product names do not establish independently implemented or commercially validated products.

The [portfolio engineering standards](docs/ENGINEERING_STANDARDS.md) guide implementation, testing, credential handling and evidence requirements across this mission.

## Protect future changes

Python 3.10+, Git, and Windows x64 or Linux x64:

```text
python tools/security_guard.py install
git -C path/to/project add -- reviewed-file.ext
python tools/security_guard.py scan --repo path/to/project
python -m unittest discover -s tests -v
```

The guard scans available Git history and staged changes, produces redacted findings, and refuses incomplete scans. It does not change visibility. See [credential handling and publication boundaries](docs/SECURITY.md). CI runs the guard and regression tests on Linux and Windows with pinned Actions and scanner archives.

Production hardening remains an active mission. Individual applications need their own build, deployment, security and customer acceptance evidence. Repository visibility and passing automated checks do not establish commercial readiness.

## Original provisioning plan

Execution uses the actual Antigravity v3.0.0 manifest. The older v2 and portfolio catalogs are
preserved under catalog/sources as reference catalogs. The user-provided 20-category summary
is preserved there too. Their names are not identical; no unverified aliases were invented.

- Target project repositories: 1,000.
- Observed existing repositories at planning: 75.
- Initial missing names: 925, beginning with batch 16 (zk-recursive).
- New project visibility: private.
- Creation method: GitHub template generation with serial requests and rate-limit handling.
- Existing projects are preserved.

The flagship hub is additional to the 1,000 project names.

## Progress

The execution worker writes a local durable journal and progress.json, then publishes a final
execution-result.json here when the run finishes. Presence, scaffold initialization, real
implementation, testing, security approval, and production readiness are separate statuses.

No deployment, paid cloud service, blockchain transaction, or GitHub Actions workflow is
created by this initialization run. A basic scaffold is not a finished cryptocurrency product.

## Catalog

- catalog/canonical.json: canonical names and planning settings.
- catalog/source-map.json: domains, batches, families, and roles.
- catalog/execution-plan.json: the current 1,000-name offline preview; it cannot authorize creation.
- catalog/reference-comparison.json: differences among the reference catalogs.
- project-template/: the exact starter files copied into new repositories.

## Historical catalog preview

Python 3.10+ and a gh auth session or GH_TOKEN are required. Never store credentials here.

Default preview:
    python tools/provision.py

The original initializer is retained for reproducibility. Its private/scaffold settings
describe the creation plan, not current account visibility. Current hardening does not
create another set of repositories. Use the security guard above for ongoing checks.

## Cryptocurrency scope and plan refresh

Manifest validation rejects excluded central-bank asset references before planning or execution. Cryptocurrency tokens, wallets, stablecoins and decentralized finance remain supported.

The checked-in execution plan is regenerated from the current canonical cryptocurrency catalog as an offline preview, including its manifest checksum, scaffold hashes, engine checksum and plan ID. It carries no current inventory or creation authorization. Generate and review a fresh live plan against current inventory before provisioning; historical approvals and provisioning journals cannot be reused with this plan.

