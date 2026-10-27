# QMOOSA-1000 — sampled current-default-HEAD CI verification (2026-10-25)

**Scope:** 15 specifically sampled original owner repositories, not a portfolio-wide acceptance claim.

For each row, the GitHub `main` branch HEAD SHA was read from GitHub's branch endpoint and compared to the `head_sha` of completed GitHub Actions runs on the `main` branch. All matching runs returned SUCCESS in this sample. This establishes a current-HEAD workflow result, **not** independent security review, FIPS validation, full implementation completeness, or deployment readiness.

| Repository | Current `main` SHA | Matching GitHub Actions run | Observed conclusion |
|---|---|---|---|
| [`qmoosa-pqc-hybrid-tls-protocol`](https://github.com/elon00/qmoosa-pqc-hybrid-tls-protocol) | `f2e2a73688849190ee231bf887a2dbcc29324eda` | [39169456197](https://github.com/elon00/qmoosa-pqc-hybrid-tls-protocol/actions/runs/39169456197) | SUCCESS |
| [`qmoosa-pqc-hybrid-tls-engine`](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine) | `75cd0e61e16cb169c3c9e47ebd99150a39f141d7` | [39312562674](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/39312562674) | SUCCESS |
| [`qmoosa-pqc-hybrid-tls-sdk`](https://github.com/elon00/qmoosa-pqc-hybrid-tls-sdk) | `97a11a9e128a50bc52815716c80501f65f24e419` | [39169895366](https://github.com/elon00/qmoosa-pqc-hybrid-tls-sdk/actions/runs/39169895366) | SUCCESS |
| [`qmoosa-pqc-hybrid-tls-dashboard`](https://github.com/elon00/qmoosa-pqc-hybrid-tls-dashboard) | `cd02963a4762ef1a9dbbc69c50e398b6cb08d4e3` | [39170027426](https://github.com/elon00/qmoosa-pqc-hybrid-tls-dashboard/actions/runs/39170027426) | SUCCESS |
| [`qmoosa-pqc-hybrid-tls-tests`](https://github.com/elon00/qmoosa-pqc-hybrid-tls-tests) | `320fb517045388679d940a416d1b2c6a3d10f411` | [39170506228](https://github.com/elon00/qmoosa-pqc-hybrid-tls-tests/actions/runs/39170506228) | SUCCESS |
| [`qmoosa-zk-groth16-protocol`](https://github.com/elon00/qmoosa-zk-groth16-protocol) | `9b7f29227196b57f2c3d9f52cb123f72c5fd6afc` | [39171872238](https://github.com/elon00/qmoosa-zk-groth16-protocol/actions/runs/39171872238) | SUCCESS |
| [`qmoosa-zk-groth16-engine`](https://github.com/elon00/qmoosa-zk-groth16-engine) | `cf5c89997aeda70171b6e696960d26930277fd68` | [39175225402](https://github.com/elon00/qmoosa-zk-groth16-engine/actions/runs/39175225402) | SUCCESS |
| [`qmoosa-zk-groth16-sdk`](https://github.com/elon00/qmoosa-zk-groth16-sdk) | `de5e7f922f715ddbe0b7b4e4f1cf6cdef3e31f65` | [39175296659](https://github.com/elon00/qmoosa-zk-groth16-sdk/actions/runs/39175296659) | SUCCESS |
| [`qmoosa-zk-groth16-dashboard`](https://github.com/elon00/qmoosa-zk-groth16-dashboard) | `4592ccf8f076e07434ec006c6c97ebf9bce3a9b7` | [39173396017](https://github.com/elon00/qmoosa-zk-groth16-dashboard/actions/runs/39173396017) | SUCCESS |
| [`qmoosa-zk-groth16-tests`](https://github.com/elon00/qmoosa-zk-groth16-tests) | `b1410e74cd5931aa1a0d9861446f0aab469d1cd4` | [39259181349](https://github.com/elon00/qmoosa-zk-groth16-tests/actions/runs/39259181349) | SUCCESS |
| [`qmoosa-pqc-slhdsa-protocol`](https://github.com/elon00/qmoosa-pqc-slhdsa-protocol) | `75784c7a219acce053b00d4e0d483182573af374` | [39166683906](https://github.com/elon00/qmoosa-pqc-slhdsa-protocol/actions/runs/39166683906) | SUCCESS |
| [`qmoosa-pqc-slhdsa-engine`](https://github.com/elon00/qmoosa-pqc-slhdsa-engine) | `41f8afa3a32af2a03e004c340e12ed77085488f5` | [39167083661](https://github.com/elon00/qmoosa-pqc-slhdsa-engine/actions/runs/39167083661) | SUCCESS |
| [`qmoosa-pqc-slhdsa-sdk`](https://github.com/elon00/qmoosa-pqc-slhdsa-sdk) | `0b7aa112881c83c68b1b0a80303a35d17894facd` | [39167398912](https://github.com/elon00/qmoosa-pqc-slhdsa-sdk/actions/runs/39167398912) | SUCCESS |
| [`qmoosa-pqc-slhdsa-dashboard`](https://github.com/elon00/qmoosa-pqc-slhdsa-dashboard) | `5cbb4fa8073b0869bf4eddb7a9d6da492dcfdf05` | [39167554682](https://github.com/elon00/qmoosa-pqc-slhdsa-dashboard/actions/runs/39167554682) | SUCCESS |
| [`qmoosa-pqc-slhdsa-tests`](https://github.com/elon00/qmoosa-pqc-slhdsa-tests) | `c43cd5fdbdd13d6bfa616ee9c0318f9ada84aac0` | [39167949412](https://github.com/elon00/qmoosa-pqc-slhdsa-tests/actions/runs/39167949412) | SUCCESS |

**Sampled CI_VERIFIED: 15/15**. Portfolio-wide count remains unverified; no claim is made for the other 985 approved entries. GitHub workflow results are from their recorded run dates and were rechecked against the unchanged `main` HEAD on 2026-10-25.

**Important exception:** Batch 14 hybrid TLS engine's **unmerged PR head** `ffc39df0a9f044b367c13ef588b772174e71cd6c` has [failed CI #40162001709](https://github.com/elon00/qmoosa-pqc-hybrid-tls-engine/actions/runs/40162001709), 38/39 tests passing, because a new two-process AES-GCM key/IV reuse regression correctly detects a P1 blocker. The main-branch SUCCESS is not evidence that the PR head or the raw record adapter is security approved.

No paid operations, public deployments, force-push or certification.
