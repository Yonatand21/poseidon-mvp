# AGENTS.md - Hard Rules for Automated and Human Contributors

This file encodes non-negotiable architectural invariants from `SYSTEM_DESIGN.md`.
Automated agents and human contributors are both bound by these rules.
Violations block merge.

---

## 1. Layer separation

The platform is stratified into four layers. Layers never bypass each other.

- Layer 1: simulation truth and sensor generation (`env_service`, `world_generator`, `auv_sim`, `ssv_sim`, `sensor_models`, `coupling`).
- Layer 2: classical control and safety (`nav`, `autonomy_auv`, `autonomy_ssv`).
- Layer 3: AI augmentation, advisory only (`poseidon-sim/ai/**`).
- Layer 4: evaluation AI, offline only (`poseidon-sim/evaluation/ai/**`).

### Rule 1.1 - Actuator authority is singular per vehicle

Only `poseidon-sim/autonomy_auv/**` and `poseidon-sim/autonomy_ssv/**` may publish:

- `/auv/thruster_cmd`
- `/auv/fin_cmd`
- `/ssv/thruster_cmd`
- `/ssv/rudder_cmd`

No Layer 3 or Layer 4 module may publish actuator commands.

### Rule 1.2 - Dual runtime authority boundaries

- DAVE runtime is the authority for AUV ground truth and AUV sensor truth.
- VRX runtime is the authority for SSV ground truth and SSV sensor truth.
- Cross-runtime phase/event ordering authority belongs to the federation bridge in `poseidon-sim/coupling/**`.

No other module may invent cross-runtime synchronization semantics.

### Rule 1.3 - AI is advisory, never authoritative

`poseidon-sim/ai/**` modules:

- MUST NOT publish actuator topics.
- MUST NOT be hard dependencies of Layer 2 modules.
- MUST emit model version/hash/seed metadata on advisories.
- MUST tolerate timeout/failure without degrading Layer 2 control availability.

### Rule 1.4 - Failsafes are unconditional

Safety invariants in `autonomy_auv` and `autonomy_ssv` evaluate unconditionally.
Layer 3/4 signals cannot disable, delay, or silence them.

### Rule 1.5 - Ground truth usage boundaries

Ground truth topics (`/auv/state`, `/ssv/state`) are permitted consumers only in:

- `poseidon-sim/evaluation/**`
- `poseidon-sim/coupling/**`
- `poseidon-sim/rendering/**` (read-only)

Control loops must consume Layer 2 `state_estimate` topics.

---

## 2. Determinism

For fixed scenario + seed + `ai_mode`, runs must be reproducible.

Required seed set:

- scenario seed
- DAVE runtime seed
- VRX runtime seed
- federation scheduler seed

Every MCAP must record:

- platform version
- image digests
- upstream dependency revisions
- model hashes and inference seeds (if AI enabled)

`ai_mode: off` is the regression baseline.

---

## 3. Edge posture (Profile B)

Mission-essential core must run without Unreal, without Layer 3 AI, and without outbound network.

- No runtime `apt install`, `pip install`, or model download.
- No outbound license check callbacks.
- All runtime artifacts pinned and offline-installable.
- Production manifests use digest-pinned images, not mutable tags.

---

## 4. Language boundary

- Python: orchestration, evaluation, AI inference, tooling.
- C++: timing-sensitive control paths, runtime bridges, critical sensor pipelines.
- Python failures must not take Layer 2 control offline.

---

## 5. Coding conventions

- No emojis in code or comments.
- Comments explain non-obvious constraints and trade-offs.
- Each module keeps a `README.md` aligned with current architecture.
- Scenario and vehicle configs are data-only formats (YAML/JSON/TOML).

---

## 6. Review and merge

- PRs must pass CI.
- PRs touching autonomy or AI require CODEOWNERS review.
- No force-push to `main`.
- No hook bypass flags unless explicitly approved.
- Conventional Commits preferred (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

---

## Cross-references

- `SYSTEM_DESIGN.md`
- `INFRASTRUCTURE_DESIGN.md`
- `OPEN_SOURCE_STACK.md`
