# QMOOSA-1000 — Current default-branch HEAD CI sample (2026-10-24)

Scope: 15 approved, original-family repositories in ML-KEM, Hybrid TLS and Groth16. These are **sampled CI statuses**, not a portfolio-wide security or implementation certification.

Method: connected GitHub API read `/repos/elon00/{repo}/branches/main` for current HEAD and `/repos/elon00/{repo}/actions/runs?branch=main&per_page=5`. For each row, the observed successful push run's `head_sha` exactly equaled the observed `main` HEAD. Results are a point-in-time snapshot and can become stale on new commits.

| Repository | Observed main SHA | Matching SUCCESS workflow run |
|---|---|---|
| [qmoosa-pqc-mlkem-protocol](https://github.com/elon00/qmoosa-pqc-mlkem-protocol) | `ba2ee330c7457097f686723de87984b3008da0fd` | [39159502636](https://github.com/elon00/qmoosa-pqc-mlkem-protocol/actions/runs/39159502636) |
| [qmoosa-pqc-mlkem-engine](https://github.com/elon00/qmoosa-pqc-mlkem-engine) | `10d9c785038062c7ce728cccca8f3264f36d4f97` | [39163434193](https://github.com/elon00/qmoosa-pqc-mlkem-engine/actions/runs/39163434193) |
| [qmoosa-pqc-mlkem-sdk](https://github.com/elon00/qmoosa-pqc-mlkem-sdk) | `37fff8e3c77e938ba48111b9a6035928678c50c7` | [39163247783](https://github.com/elon00/qmoosa-pqc-mlkem-sdk/actions/runs/39163247783) |
| [qmoosa-pqc-mlkem-dashboard](https://github.com/elon00/qmoosa-pqc-mlkem-dashboard) | `f14d3860f633f74a530c2a40231b50024111aba3` | [39160864378](https://github.com/elon00/qmoosa-pqc-mlkem-dashboard/actions/runs/39160864378) |
| [qmoosa-pqc-mlkem-tests](https://github.com/elon00/qmoosa-pqc-mlkem-tests) | `86f9a5f01c1a678d3173ee00aac78839cf20252c` | [39163697448](https://github.com/elon00/qmoosa-pqc-mlkem-tests/actions/runs/39163697448) |
| [qmoosa-pqc-hybrid-tls-protocol](https://github.com/elon00/qmoosa-pqc-hybrid-tls-protocol) | `f2e2a73688849190ee231bf887a2dbcc29324eda` | [39169456197](https://github.com/elon00/qmoosa-pqc-hybrid-tls-protocol/actions/runs/39169456197) |
| [qmoosa-pqc-hybrid-tls-engine](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine) | `75cd0e61e16cb169c3c9e47ebd99150a39f141d7` | [39312562674](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/39312562674) |
| [qmoosa-pqc-hybrid-tls-sdk](https://github.com/elon00/qmoosa-pqc-hybrid-tls-sdk) | `97a11a9e128a50bc52815716c80501f65f24e419` | [39169895366](https://github.com/elon00/qmoosa-pqc-hybrid-tls-sdk/actions/runs/39169895366) |
| [qmoosa-pqc-hybrid-tls-dashboard](https://github.com/elon00/qmoosa-pqc-hybrid-tls-dashboard) | `cd02963a4762ef1a9dbbc69c50e398b6cb08d4e3` | [39170027426](https://github.com/elon00/qmoosa-pqc-hybrid-tls-dashboard/actions/runs/39170027426) |
| [qmoosa-pqc-hybrid-tls-tests](https://github.com/elon00/qmoosa-pqc-hybrid-tls-tests) | `320fb517045388679d940a416d1b2c6a3d10f411` | [39170506228](https://github.com/elon00/qmoosa-pqc-hybrid-tls-tests/actions/runs/39170506228) |
| [qmoosa-zk-groth16-protocol](https://github.com/elon00/qmoosa-zk-groth16-protocol) | `9b7f29227196b57f2c3d9f52cb123f72c5fd6afc` | [39171872238](https://github.com/elon00/qmoosa-zk-groth16-protocol/actions/runs/39171872238) |
| [qmoosa-zk-groth16-engine](https://github.com/elon00/qmoosa-zk-groth16-engine) | `cf5c89997aeda70171b6e696960d26930277fd68` | [39175225402](https://github.com/elon00/qmoosa-zk-groth16-engine/actions/runs/39175225402) |
| [qmoosa-zk-groth16-sdk](https://github.com/elon00/qmoosa-zk-groth16-sdk) | `de5e7f922f715ddbe0b7b4e4f1cf6cdef3e31f65` | [39175296659](https://github.com/elon00/qmoosa-zk-groth16-sdk/actions/runs/39175296659) |
| [qmoosa-zk-groth16-dashboard](https://github.com/elon00/qmoosa-zk-groth16-dashboard) | `4592ccf8f076e07434ec006c6c97ebf9bce3a9b7` | [39173396017](https://github.com/elon00/qmoosa-zk-groth16-dashboard/actions/runs/39173396017) |
| [qmoosa-zk-groth16-tests](https://github.com/elon00/qmoosa-zk-groth16-tests) | `b1410e74cd5931aa1a0d9861446f0aab469d1cd4` | [39259181349](https://github.com/elon00/qmoosa-zk-groth16-tests/actions/runs/39259181349) |

**Result:** 15/15 sampled current-HEAD successful workflow runs; no claim that these are all 1,000 repositories or that all relevant security suites were executed. CI success does not imply cryptographic/FIPS validation, adversarial test completeness, or production readiness. Hybrid TLS draft PR #2 remains unmerged and has unresolved key/nonce reuse and crash recovery findings.

No new main branch commits, deployments, paid resources, force pushes, or merges in this verification.
