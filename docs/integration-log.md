# Integration log

Living cross-track tracker for the three parallel workstreams taking
POSEIDON from Tier-1 mock backbone to Tier-3 federated DAVE + VRX with
Tier-2 evaluation coverage. Owned collectively; every owner is expected
to append to the daily log section.

- Track A: AUV runtime integration - `docs/runbooks/integration-auv-dave.md`
- Track B: SSV runtime integration - `docs/runbooks/integration-ssv-vrx.md`
- Track C: Tier-2 evaluation + contract gate - `docs/runbooks/tier-2-evaluation.md`

The single integration seam for all three is the Section 14 topic
contract in `SYSTEM_DESIGN.md`. It is enforced by:

- `tests/integration/test_runtime_contract.py` on the live ROS graph.
- `python3 -m evaluation.metrics.extract --strict` on recorded MCAPs.

Both are expected to be green before any runtime PR merges.

---

## Track status

Update the row you own at the end of each working session.

| Track | Owner | Branch | Day | Status | Blocker | Last update |
| --- | --- | --- | --- | --- | --- | --- |
| A - AUV DAVE | Robert | `feat/auv-dave-integration` | 0 | kickoff | base-image PR | 2026-04-18 |
| B - SSV VRX | John | `feat/ssv-vrx-integration` | 0 | kickoff | base-image PR | 2026-04-18 |
| C - Tier-2 eval | Yonatan | `feat/tier-2-evaluation` | 1 | registry + CLI shipped | none | 2026-04-18 |

---

## Dependency graph

```text
                   +-----------------------------+
                   | base-image PR (Gazebo H.)   |  blocks A and B
                   +--------------+--------------+
                                  |
                 +----------------+----------------+
                 |                                 |
                 v                                 v
   +-----------------------------+   +-----------------------------+
   | Track A: AUV DAVE runtime   |   | Track B: SSV VRX runtime    |
   +--------------+--------------+   +--------------+--------------+
                  \\                                 /
                   \\       Section 14 contract     /
                    v        (kpis.json + --strict)
                   +-----------------------------+
                   | Track C: Tier-2 evaluation  |  runs in parallel;
                   | extractor + dashboard       |  also the CI gate
                   +-----------------------------+  for A and B PRs
```

Track C does not wait for A or B to start. Track C Day-1 (registry +
`--strict` CLI) is a soft blocker on A and B merge - neither track can
cite a green contract check in their PR description without it.

---

## PR sequence and merge gates

| PR | From | Tier gate (AGENTS + backbone-verification.md) |
| --- | --- | --- |
| base-image: Gazebo Harmonic in `base-dev.Dockerfile` | A or B (first mover) | T0 + T1 on Mac |
| Track C Day 1-2: `evaluation/metrics` + `--strict` CLI | C | T0 + `pytest tests/unit/test_metrics_registry.py` |
| Track A: `sim-auv-dave.Dockerfile` + launch remap | A | T0 + T1 on Linux + `--strict` contract-check |
| Track B: `sim-ssv-vrx.Dockerfile` + launch remap | B | T0 + T1 on Linux + `--strict` contract-check |
| Track C Day 3: Streamlit dashboard consumes `kpis.json` | C | T0 + T2 on Mac |

Every runtime PR (A or B) MUST paste into the PR description:

1. `tools/verify-backbone-t1.sh` tail (last 20 lines including `[DONE]`).
2. `tests/integration/test_runtime_contract.py --vehicle <auv|ssv>` output.
3. `python3 -m evaluation.metrics.extract --mcap <recording> --strict` output.

No exceptions - this is how Tier-3 stays coherent.

---

## Contract checklist (copy into runtime PRs)

```markdown
- [ ] Topic names preserved (remap only, per AGENTS.md Rule 1.1)
- [ ] No Layer 3/4 actuator publications introduced
- [ ] `verify-backbone-t1.sh` exits 0 on the target host
- [ ] `tests/integration/test_runtime_contract.py` exits 0
- [ ] `evaluation.metrics.extract --strict` exits 0 against a fresh recording
- [ ] `kpis.json` schema_version matches `SCHEMA_VERSION` in `evaluation/metrics/schema.py`
- [ ] MCAP recording attached or linked in PR description
- [ ] No digest-pinned image tags replaced with mutable tags (AGENTS.md Section 3)
```

---

## Decision log

Append a dated entry per non-obvious decision. Reference ADR if one is
written.

| Date | Scope | Decision | Rationale / link |
| --- | --- | --- | --- |
| 2026-04-18 | Track C | `kpis.json` schema versioned (`SCHEMA_VERSION = 1`) | Lets runtimes evolve without breaking the dashboard; mcap-only consumers migrate on bump |
| 2026-04-18 | Track C | `mcap` libs live under `[project.optional-dependencies.eval]`, not core | Keeps mission-essential core pip-dep free (AGENTS.md Section 3) |
| TBD | A + B | Ocean forcing schema for `/env/current` and `/env/wave_state` | Open question #2 in `SYSTEM_DESIGN.md`; both runtimes must agree. ADR pending: `docs/architecture/0002-ocean-forcing-schema.md` |
| TBD | A | DAVE upstream pin (commit SHA) | Record once cloud-box build succeeds |
| TBD | B | VRX upstream pin (commit SHA) | Record once cloud-box build succeeds |

---

## Daily log

One line per track per working day. Format:

```text
YYYY-MM-DD | <track letter> | <owner> | <status in one sentence>
```

```text
2026-04-18 | C | Yonatan | registry + --strict CLI + unit tests landed on feat/tier-2-evaluation
2026-04-18 | A | Robert  | kickoff; reading integration-auv-dave.md runbook
2026-04-18 | B | John    | kickoff; reading integration-ssv-vrx.md runbook
```
