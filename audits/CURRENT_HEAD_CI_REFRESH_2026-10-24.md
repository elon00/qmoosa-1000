# Current default-branch HEAD CI refresh — 2026-10-24

All 15 repositories below had their `main` branch SHA read from GitHub and matched to a completed SUCCESS GitHub Actions workflow run on that same SHA. The connector was queried on 2026-10-24. This is a **sample**, not a portfolio-wide count; successful workflow status is **not** proof of implementation-coupled testing, FIPS validation, security acceptance or production readiness.

| Repository | Observed main HEAD SHA | Matching successful Actions run |
|---|---|---|
| `qmoosa-pqc-hybrid-tls-protocol` | `f2e2a73688849190ee231bf887a2dbcc29324eda` | [39169456197](https://github.com/elon00/qmoosa-pqc-hybrid-tls-protocol/actions/runs/39169456197) |
| `qmoosa-pqc-hybrid-tls-engine` | `75cd0e61e16cb169c3c9e47ebd99150a39f141d7` | [39312562674](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/39312562674) |
| `qmoosa-pqc-hybrid-tls-sdk` | `97a11a9e128a50bc52815716c80501f65f24e419` | [39169895366](https://github.com/elon00/qmoosa-pqc-hybrid-tls-sdk/actions/runs/39169895366) |
| `qmoosa-pqc-hybrid-tls-dashboard` | `cd02963a4762ef1a9dbbc69c50e398b6cb08d4e3` | [39170027426](https://github.com/elon00/qmoosa-pqc-hybrid-tls-dashboard/actions/runs/39170027426) |
| `qmoosa-pqc-hybrid-tls-tests` | `320fb517045388679d940a416d1b2c6a3d10f411` | [39170506228](https://github.com/elon00/qmoosa-pqc-hybrid-tls-tests/actions/runs/39170506228) |
| `qmoosa-pqc-mlkem-protocol` | `ba2ee330c7457097f686723de87984b3008da0fd` | [39159502636](https://github.com/elon00/qmoosa-pqc-mlkem-protocol/actions/runs/39159502636) |
| `qmoosa-pqc-mlkem-engine` | `10d9c785038062c7ce728cccca8f3264f36d4f97` | [39163434193](https://github.com/elon00/qmoosa-pqc-mlkem-engine/actions/runs/39163434193) |
| `qmoosa-pqc-mlkem-sdk` | `37fff8e3c77e938ba48111b9a6035928678c50c7` | [39163247783](https://github.com/elon00/qmoosa-pqc-mlkem-sdk/actions/runs/39163247783) |
| `qmoosa-pqc-mlkem-dashboard` | `f14d3860f633f74a530c2a40231b50024111aba3` | [39160864378](https://github.com/elon00/qmoosa-pqc-mlkem-dashboard/actions/runs/39160864378) |
| `qmoosa-pqc-mlkem-tests` | `86f9a5f01c1a678d3173ee00aac78839cf20252c` | [39163697448](https://github.com/elon00/qmoosa-pqc-mlkem-tests/actions/runs/39163697448) |
| `qmoosa-zk-groth16-protocol` | `9b7f29227196b57f2c3d9f52cb123f72c5fd6afc` | [39171872238](https://github.com/elon00/qmoosa-zk-groth16-protocol/actions/runs/39171872238) |
| `qmoosa-zk-groth16-engine` | `cf5c89997aeda70171b6e696960d26930277fd68` | [39175225402](https://github.com/elon00/qmoosa-zk-groth16-engine/actions/runs/39175225402) |
| `qmoosa-zk-groth16-sdk` | `de5e7f922f715ddbe0b7b4e4f1cf6cdef3e31f65` | [39175296659](https://github.com/elon00/qmoosa-zk-groth16-sdk/actions/runs/39175296659) |
| `qmoosa-zk-groth16-dashboard` | `4592ccf8f076e07434ec006c6c97ebf9bce3a9b7` | [39173396017](https://github.com/elon00/qmoosa-zk-groth16-dashboard/actions/runs/39173396017) |
| `qmoosa-zk-groth16-tests` | `b1410e74cd5931aa1a0d9861446f0aab469d1cd4` | [39259181349](https://github.com/elon00/qmoosa-zk-groth16-tests/actions/runs/39259181349) |

Separate evidence: [Batch 14 TLS engine PR-head run 40089091667](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/40089091667) SUCCESS on `b243de73660d102e9b3936721a73f6996df48eaf`, **not** default branch. That PR still has unresolved cross-process/distributed nonce-lifecycle risk.

CI_VERIFIED (sampled, current default HEAD): **15**. IMPLEMENTED: not portfolio-verified. SECURITY_APPROVED: 0 independently evidenced. DEPLOYMENT_READY: 0 independently evidenced. Production-certified: 0 independently evidenced.
