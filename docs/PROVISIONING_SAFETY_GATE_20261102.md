# P1 live provisioning identity gate — 2026-11-02

Scope: approved canonical `catalog/canonical.json` only, owner `elon00`. This change is a **fail-closed safety remediation**, not permission to create repositories or change their visibility.

- `make_plan` rejects canonical forks, missing/duplicate IDs, duplicate names, nonboolean visibility, unexpected owner/full-name metadata and visibility mismatches. Unrelated owner repositories do not count toward the 1,000.
- `apply_plan` compares the latest canonical identity snapshot against the reviewed plan **before any remote writes**, then refuses unexpected repositories discovered after the snapshot. The flagship `tools/provision.py` path performs the same preflight and refuses unplanned matches.
- `tests/test_live_plan_identity.py` covers real code with offline adversarial fixtures. Fixture PASS is not live GitHub identity verification or product implementation evidence.
- `catalog/execution-plan.json` was re-checksummed for the changed engine code and remains **offline preview only** (`mode=offline`, `inventory=null`); it is not an approved live provisioning plan.
- Canonical visibility remains `private: true` from generator defaults, not owner-approved policy. Existing public canonical repositories therefore block live planning by design until [issue #18](https://github.com/elon00/qmoosa-1000/issues/18) is resolved. Do not weaken the gate to force progress.
- This review does not approve any repository creation, secret access, mainnet/testnet deployment, paid runner, cryptographic certification, or production readiness.

Run locally without credentials: `python -m unittest discover -s tests -v`. Review exact PR-head GitHub Actions and independent security acceptance before merge. Do not run `apply` or `tools/provision.py --execute`.
