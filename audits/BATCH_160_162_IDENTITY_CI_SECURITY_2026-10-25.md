# QMOOSA-1000 — Batches 160–162 identity and security checkpoint

Date: 2026-10-25. Status: **AUDIT ONLY — NOT PRODUCTION CERTIFIED**.

## Authority and method

- Manifest: `catalog/canonical.json` at blob `0f025faae374aaf8388e5e0652df994bbd20d00a`, parsed as 1,000 unique approved repository names.
- Each of the 15 entries was cross-referenced to its `QMOOSA-0796`–`QMOOSA-0810` canonical architecture ID via GitHub code search, owner `elon00`, and stable GitHub repository ID from repository metadata.
- All 15 were returned by owner-scoped GitHub repository search with `fork:false`. The three families have five components each; all stable IDs are distinct. No forks or unrelated repositories counted.
- All 15 actual repositories are **public** although their manifest entries specify `private: true`; visibility policy and sensitive-content exposure require review. Do not silently change visibility.

| Batch | Architecture ID | Approved manifest name | Actual original repository | Stable GitHub ID |
|---|---|---|---|---|
| 160 | QMOOSA-0796 | `qmoosa-sec-reality-gates-protocol` | [elon00/secgate](https://github.com/elon00/secgate) | 1425933076 |
| 160 | QMOOSA-0797 | `qmoosa-sec-reality-gates-engine` | [elon00/secgate-run](https://github.com/elon00/secgate-run) | 1425933275 |
| 160 | QMOOSA-0798 | `qmoosa-sec-reality-gates-sdk` | [elon00/secgate-kit](https://github.com/elon00/secgate-kit) | 1425933457 |
| 160 | QMOOSA-0799 | `qmoosa-sec-reality-gates-dashboard` | [elon00/secgate-lens](https://github.com/elon00/secgate-lens) | 1425933671 |
| 160 | QMOOSA-0800 | `qmoosa-sec-reality-gates-tests` | [elon00/secgate-gate](https://github.com/elon00/secgate-gate) | 1425933864 |
| 161 | QMOOSA-0801 | `qmoosa-staking-lsd-vault-protocol` | [elon00/liquidst](https://github.com/elon00/liquidst) | 1425934101 |
| 161 | QMOOSA-0802 | `qmoosa-staking-lsd-vault-engine` | [elon00/liquidst-run](https://github.com/elon00/liquidst-run) | 1425934326 |
| 161 | QMOOSA-0803 | `qmoosa-staking-lsd-vault-sdk` | [elon00/liquidst-kit](https://github.com/elon00/liquidst-kit) | 1425934578 |
| 161 | QMOOSA-0804 | `qmoosa-staking-lsd-vault-dashboard` | [elon00/liquidst-lens](https://github.com/elon00/liquidst-lens) | 1425934911 |
| 161 | QMOOSA-0805 | `qmoosa-staking-lsd-vault-tests` | [elon00/liquidst-gate](https://github.com/elon00/liquidst-gate) | 1425935081 |
| 162 | QMOOSA-0806 | `qmoosa-staking-restaking-mesh-protocol` | [elon00/eigenmesh](https://github.com/elon00/eigenmesh) | 1425935334 |
| 162 | QMOOSA-0807 | `qmoosa-staking-restaking-mesh-engine` | [elon00/eigenmesh-run](https://github.com/elon00/eigenmesh-run) | 1426537453 |
| 162 | QMOOSA-0808 | `qmoosa-staking-restaking-mesh-sdk` | [elon00/eigenmesh-kit](https://github.com/elon00/eigenmesh-kit) | 1426537617 |
| 162 | QMOOSA-0809 | `qmoosa-staking-restaking-mesh-dashboard` | [elon00/eigenmesh-lens](https://github.com/elon00/eigenmesh-lens) | 1425935710 |
| 162 | QMOOSA-0810 | `qmoosa-staking-restaking-mesh-tests` | [elon00/eigenmesh-gate](https://github.com/elon00/eigenmesh-gate) | 1425935977 |

## CI failures — direct GitHub Actions evidence

- [secgate-gate CI #40064834892](https://github.com/elon00/secgate-gate/actions/runs/40064834892): **FAILED**, CodeQL `analyze@v3` invoked without `init`; [CodeQL workflow #40064834868](https://github.com/elon00/secgate-gate/actions/runs/40064834868) **FAILED** because `actions/checkout@4` and `github/codeql-action@3` are invalid references.
- [liquidst-gate CI #40062440671](https://github.com/elon00/liquidst-gate/actions/runs/40062440671): **FAILED**, CodeQL config not initialized.
- [eigenmesh-gate CI #40060272222](https://github.com/elon00/eigenmesh-gate/actions/runs/40060272222): **FAILED**, CodeQL config not initialized.
- All three default-branch `tests/reality_battery.py` files have an identical invalid `U+0004` byte/control character in Python source. This is not a valid regression suite; do not delete, skip, or replace with trivial assertions.
- `secgate-gate/tests/reality_check_harness.py` contains `assert True` and synthetic `status: 200` checks; it cannot substantiate PQC, relayer, escrow, or production-security claims. Existing README `100/100`/FIPS badges are unsubstantiated.

## P1 security blocker: Batch 14

- [Hybrid TLS engine PR #2](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/pull/2) latest [CI #40162001709](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/40162001709) is **FAILED**: 38 tests pass, one real two-process adversarial regression fails, showing the in-process AES-GCM outbound key/IV registry does not persist across processes.
- Raw record helper is explicitly not an RFC 8446 authenticated transport; no FIPS/TLS certification or independent security approval. Require durable cross-process key/nonce uniqueness or remove the raw adapter from deployable paths, with genuine negative tests.

## Portfolio score accounting

- Previously documented lower bound: 646/1,000 identity-matched. This audit adds **15 unique identities**, yielding **661/1,000 cumulative identity-matched lower bound**, *not* an exhaustive inventory recount.
- `CREATED` is identity-matched repository existence, not implementation completion.
- `IMPLEMENTED`: portfolio-wide count not independently verified.
- `CI_VERIFIED`: 15 previously sampled default-HEAD successes; **not rechecked** in this iteration.
- `SECURITY_APPROVED`, `DEPLOYMENT_READY`, `PRODUCTION_CERTIFIED`: **0 independently evidenced**.
- No PR merged, no public deployment, no gas/cycles, no force-push. Fail-closed CI remediation requires review; no fake green claims.
