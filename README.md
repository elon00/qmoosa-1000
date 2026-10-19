# QMOOSA-1000 Flagship

One portfolio hub for 1,000 canonical project repositories.

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
- catalog/execution-plan.json: the reviewed 1,000-name create/skip plan.
- catalog/reference-comparison.json: differences among the reference catalogs.
- project-template/: the exact starter files copied into new repositories.

## Run locally

Python 3.10+ and a gh auth session or GH_TOKEN are required. Never store credentials here.

Default preview:
    python tools/provision.py

Start or resume the authorized run:
    python tools/provision.py --execute --limit 1000

The worker checks repository identity, pins the template branch, verifies file hashes,
preserves existing repositories, and stops on API errors or rate-limit rejection.
