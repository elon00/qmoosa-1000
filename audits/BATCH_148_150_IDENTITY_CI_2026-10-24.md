# QMOOSA-1000 — Batch 148–150 identity and CI checkpoint (2026-10-24)

## Method and evidence standard

- Source of approval: `catalog/canonical.json` on `elon00/qmoosa-1000` main, SHA of file `0f025faae374aaf8388e5e0652df994bbd20d00a`. Parsed 1,000 entries and 1,000 unique names.
- For each counted entry, an old canonical repository URL was resolved by the authenticated GitHub repository endpoint to the same **stable GitHub repository ID** as the current name. Current owner `elon00`, `fork=false`, `archived=false` were checked via GitHub repository metadata.
- These 12 identity matches prove repository existence/identity only. They do NOT prove implementation, CI, security acceptance, or deployment readiness.
- The approved manifest declares `private: true` for these entries; all 12 currently resolve to **public** repositories. Human visibility-policy review required before further provisioning.

| Batch | Approved manifest name | Current GitHub name | Stable GitHub ID | Identity |
|---|---|---|---:|---|
| 148 | qmoosa-game-spatial-anchors-dashboard | spatialx-lens | 1425920107 | VERIFIED |
| 148 | qmoosa-game-spatial-anchors-tests | spatialx-gate | 1425920315 | VERIFIED |
| 149 | qmoosa-game-tournament-escrow-protocol | tourney | 1425920501 | VERIFIED |
| 149 | qmoosa-game-tournament-escrow-engine | tourney-run | 1425920687 | VERIFIED |
| 149 | qmoosa-game-tournament-escrow-sdk | tourney-kit | 1425920888 | VERIFIED |
| 149 | qmoosa-game-tournament-escrow-dashboard | tourney-lens | 1425921084 | VERIFIED |
| 149 | qmoosa-game-tournament-escrow-tests | tourney-gate | 1425921271 | VERIFIED |
| 150 | qmoosa-game-reality-gates-protocol | gamegate | 1425921489 | VERIFIED |
| 150 | qmoosa-game-reality-gates-engine | gamegate-run | 1425921702 | VERIFIED |
| 150 | qmoosa-game-reality-gates-sdk | gamegate-kit | 1425921881 | VERIFIED |
| 150 | qmoosa-game-reality-gates-dashboard | gamegate-lens | 1425922078 | VERIFIED |
| 150 | qmoosa-game-reality-gates-tests | gamegate-gate | 1425922259 | VERIFIED |

## Unresolved Batch 148 identities — DO NOT COUNT

`qmoosa-game-spatial-anchors-protocol`, `qmoosa-game-spatial-anchors-engine`, and `qmoosa-game-spatial-anchors-sdk` returned HTTP 404. Candidate non-fork owner repositories `spatialx` (ID 1426533012), `spatialx-run` (ID 1426533162), and `spatialx-kit` (ID 1426533303) exist but their README/description did **not** establish a canonical architecture ID or historical rename. Do not count these 3 until provenance is independently established; do not create duplicates while unresolved.

## Current default-branch CI failures (verified 2026-10-24)

- [spatialx-gate run 40065291247](https://github.com/elon00/spatialx-gate/actions/runs/40065291247): FAILED; CodeQL `analyze` without `init`. [Other workflow 40065291228](https://github.com/elon00/spatialx-gate/actions/runs/40065291228) also FAILED.
- [tourney-gate run 40066154845](https://github.com/elon00/tourney-gate/actions/runs/40066154845): FAILED at job setup; invalid `actions/checkout@4` and `github/codeql-action@3` references.
- [gamegate-gate run 40061135646](https://github.com/elon00/gamegate-gate/actions/runs/40061135646): FAILED; CodeQL init missing. [Other workflow 40061135592](https://github.com/elon00/gamegate-gate/actions/runs/40061135592) FAILED at setup with invalid Action refs.
- [gamegate-gate draft PR #1](https://github.com/elon00/gamegate-gate/pull/1) corrects references and adds fail-closed Python compilation, pytest, and CodeQL initialization. PR-head CI must be evaluated independently. It remains draft/unmerged; existing corrupted tests remain a blocker.

## Security integrity and Batch 14

- `gamegate-gate/tests/reality_battery.py` contains invalid control characters; `tests/reality_check_harness.py` makes unsubstantiated success claims with constants/`assert True`. Do not accept as implementation-coupled tests.
- [Batch 14 TLS PR #2](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/pull/2) has [PR-head CI run 40089091667](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/40089091667) SUCCESS, but cross-process restart and distributed key/nonce uniqueness remain unresolved; no independent cryptographic acceptance or FIPS certification.
- `SECURITY_APPROVED`, `DEPLOYMENT_READY` and production-certified remain **zero independently evidenced** in this checkpoint.

## Scorecard handling

Previous checkpoint recorded **589** cumulative identity mappings. This checkpoint adds **12** independent stable-ID verified mappings for a cumulative *reported lower bound* of **601/1,000**. Prior 589 were not exhaustively revalidated in this bounded run. Implementation and current-HEAD CI portfolio totals remain unverified. No deployment, money/gas/cycles, force push, merge, or secret usage.

## Next acceptance gates

1. Resolve 3 Batch 148 aliases using stable-ID provenance (not name similarity).
2. Repair corrupted tests with real implementation-bound assertions and adversarial cases, then require PR-head CI success.
3. Resolve manifest privacy mismatch after exposure review.
4. Independently validate Batch 14 nonce lifecycle across process restarts/workers before security approval.
