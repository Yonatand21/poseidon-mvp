# AGENTS.md - Hard Rules for Automated and Human Contributors

This file encodes non-negotiable architectural invariants from `SYSTEM_DESIGN.md`.
Automated agents (Cursor, Claude, Copilot, CI linters) and human contributors
are both bound by these rules. Violations block merge.

---

## 1. Layer separation (SYSTEM_DESIGN.md Section 4.5)

The platform is stratified into four layers. Layers never bypass each other.

- **Layer 1** - Deterministic simulation truth (`poseidon-sim/env_service`, `world_generator`, `auv_sim`, `ssv_sim`, `sensor_models`, `nav/gnss_env`, `nav/acoustic_env`, `coupling`).
- **Layer 2** - Classical control and safety (`poseidon-sim/nav/auv_nav`, `nav/ssv_nav`, `autonomy_auv`, `autonomy_ssv`).
- **Layer 3** - AI augmentation, advisory only (`poseidon-sim/ai/**`).
- **Layer 4** - Evaluation AI, offline only (`poseidon-sim/evaluation/ai/**`).

### Rule 1.1 - Singular actuator authority

Only `poseidon-sim/autonomy_auv/**` and `poseidon-sim/autonomy_ssv/**` may
publish to these topics:

- `/auv/thruster_cmd`
- `/auv/fin_cmd`
- `/ssv/thruster_cmd`
- `/ssv/rudder_cmd`

No other module, and specifically no Layer 3 AI module, may publish to them.
CI enforces this with a DDS-permission lint (see `tools/check_layer_permissions.py`).

### Rule 1.2 - AI is advisory, never authoritative

`poseidon-sim/ai/**` modules:

- MUST NOT publish actuator topics.
- MUST NOT be imported as a hard dependency of any Layer 2 module.
- MUST have a Layer 2 fallback path that runs unconditionally whether or not
  the AI module is present, healthy, or timely.
- MUST record model version, file hash, and inference seed on every advisory
  published.

### Rule 1.3 - Failsafes are unconditional

Safety invariants in `poseidon-sim/autonomy_auv/safety_invariants` and
`poseidon-sim/autonomy_ssv/safety_invariants` (geofence, min-altitude,
max-depth, max-speed, abort-to-surface, return-to-launch, comms-timeout)
evaluate unconditionally. Nothing in Layer 3 or Layer 4 can weaken, delay,
or silence them.

### Rule 1.4 - Ground truth is evaluation-only

`/auv/state` and `/ssv/state` are ground-truth 6-DOF topics from Layer 1.
Only `poseidon-sim/evaluation/**` may subscribe. Control loops MUST use the
`state_estimate` topics from Layer 2, never ground truth.

---

## 2. Determinism (SYSTEM_DESIGN.md Sections 3, 10.1, 17.3)

- Every scenario run is seed-deterministic. Same scenario + same seed +
  same `ai_mode` => bit-identical ground-truth outputs.
- AI modules run with pinned weights and pinned inference seeds. If an AI
  module is non-deterministic, the scenario engine marks the run
  `ai_mode: non-deterministic` and flags it.
- Every MCAP records the full version stack (platform version, image digests,
  model hashes, scenario hash).
- `ai_mode: off` is the regression baseline. Any AI-enabled run must be
  reproducible against a classical baseline run on the same seed.

---

## 3. Profile B edge posture (SYSTEM_DESIGN.md Section 17, INFRASTRUCTURE_DESIGN.md Section 3)

Mission-essential core must run without Unreal, without Layer 3 AI, and
without network connectivity.

- No component may require runtime `apt install`, `pip install`, or model
  download from public mirrors.
- No component may require outbound network or license-check callbacks.
- Every Python package is pinned in `uv.lock` and vendorable (wheelhouse-exportable).
- Every container image is referenced by digest in production manifests,
  never by tag.

---

## 4. Language boundary (SYSTEM_DESIGN.md Section 17.3)

- Python: scenario orchestration, evaluation, AI inference only.
- C++: control loops, timing-sensitive simulation bridges, Stonefish plugins,
  critical sensor pipelines.
- Python failures MUST NOT take Layer 2 control offline.

---

## 5. Coding conventions

- No emojis in code or code comments.
- Comments explain non-obvious intent, trade-offs, or constraints. Do not
  narrate what the code does.
- Every module has a `README.md` citing the design section it implements.
- Config is data-only (YAML, JSON, TOML). No executable code in scenario
  files or vehicle configs.

---

## 6. Review and merge

- Every PR must pass CI (`.github/workflows/ci.yml`).
- Every PR touching `poseidon-sim/autonomy_*` or `poseidon-sim/ai/**`
  requires domain-owner review per `.github/CODEOWNERS`.
- No force-push to `main`. No `--no-verify` commits.
- Commit messages follow Conventional Commits when practical
  (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

---

## Cross-references

- `SYSTEM_DESIGN.md` Sections 4 (layers), 10 (AI), 17 (profiles)
- `INFRASTRUCTURE_DESIGN.md` Sections 3 (containers), 9 (security), 11 (CI/CD)
- `OPEN_SOURCE_STACK.md` Section 6 (license posture)
