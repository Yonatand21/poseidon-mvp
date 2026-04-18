# POSEIDON MVP - System Design (Federated Gazebo Runtime)

## One-line framing

POSEIDON MVP is a deterministic maritime T&E platform for coupled AUV+SSV missions under controllable ocean and navigation conditions, using DAVE (AUV), VRX (SSV), and UNav-Sim (visual/perception) over a ROS 2 federation backbone.

---

## 1. System goal

Deliver repeatable virtual trials for maritime missions where:

- Layer 2 classical control/safety is always the actuator authority.
- Layer 3 AI is advisory-only.
- Layer 4 evaluation is offline and non-authoritative.
- Same scenario + same seeds + same mode yields reproducible results.

---

## 2. Capability headlines

1. Parameterized maritime environments (bathymetry, currents, sea state, visibility, acoustic profile).
2. GNSS-denied/contested mission phases with degradation effects.
3. Coupled SSV-to-AUV mission flow with drop and recovery phases.
4. Deterministic MCAP recording and KPI reporting.
5. Perception-ready visual outputs via UNav-Sim.

---

## 3. Top-level architecture

```text
ROS 2 Mission Graph (Jazzy)
  ├─ Gazebo runtime A (DAVE): AUV physics + AUV sensors
  ├─ Gazebo runtime B (VRX):  SSV physics + SSV sensors
  ├─ Federation bridge: time sync, event ordering, runtime health
  ├─ Layer 2 nav/autonomy/safety
  ├─ Layer 3 AI advisory modules
  ├─ Layer 4 evaluation pipeline
  └─ Rendering consumers: UNav-Sim (primary), PoseidonUE (fallback)
```

Two runtimes are an explicit architecture choice, not accidental overlap.

---

## 4. Layer model

- **Layer 1**: simulation truth and sensor generation (`env_service`, `world_generator`, `auv_sim`, `ssv_sim`, `sensor_models`, `coupling`).
- **Layer 2**: classical nav/control/safety (`nav`, `autonomy_auv`, `autonomy_ssv`).
- **Layer 3**: AI augmentation (advisory only, `ai/**`).
- **Layer 4**: evaluation AI/reporting (offline only, `evaluation/**`).

Hard invariants are codified in `AGENTS.md`.

---

## 5. Environment and world generation (Layer 1)

Scenario-driven and seed-driven environment generation with archetypes:

- `open_water`
- `continental_shelf`
- `littoral`
- `choke_point`
- `harbor_approach`

Environment fields:

- bathymetry
- currents
- wave/sea state
- visibility/turbidity
- sound-speed profile
- ambient acoustic profile

`world_generator` emits runtime-specific artifacts for DAVE/VRX and render artifacts for Unreal.

---

## 6. Vehicle and asset strategy

MVP baseline:

- AUV runtime model starts from DAVE stock assets.
- SSV runtime model starts from VRX/WAM-V assets.
- Custom CAD integration is incremental, not sprint-critical.

Rules:

- Mass/inertia tracked as versioned source config.
- Runtime-specific configs are generated from canonical vehicle metadata where possible.
- Imported upstream assets include source revision and license metadata.

---

## 7. Sensor architecture

Canonical topic contracts are stable even if source implementation differs by runtime.

Key sensor streams:

- AUV: IMU, depth, DVL, USBL, camera, sonar.
- SSV: GNSS, IMU/compass, radar, camera.
- Shared degradation inputs from `env_service`, `nav/gnss_env`, and `nav/acoustic_env`.

---

## 8. Navigation and control (Layer 2)

- `robot_localization`-style state estimation per vehicle.
- Control loops consume `state_estimate`, not ground truth.
- Actuator authority:
  - AUV: `/auv/thruster_cmd`, `/auv/fin_cmd`
  - SSV: `/ssv/thruster_cmd`, `/ssv/rudder_cmd`

Safety invariants are unconditional and cannot be bypassed by AI modules.

---

## 9. AI augmentation (Layer 3)

Advisory-only modules may consume:

- UNav-Sim camera streams
- sonar and nav streams
- mission context

Target use cases:

- obstacle segmentation
- visual SLAM priors
- sonar-to-image fusion assistance
- mission risk advisories

AI outputs can influence planning inputs but never directly command actuators.

---

## 10. Federated mission coupling

`poseidon-sim/coupling` owns:

1. `/sim/auv/clock` and `/sim/ssv/clock` alignment.
2. Deterministic event sequencing for mission phases.
3. Drop-commit and cross-runtime phase synchronization.
4. Runtime health/degradation signaling.

This bridge is mission-critical in this architecture.

---

## 11. Scenario engine

Scenario YAML is the single run definition.

Responsibilities:

1. Validate scenario schema + seed inputs.
2. Generate world/env artifacts.
3. Emit DAVE/VRX/federation configs.
4. Launch graph and mission timeline.
5. Trigger fault injections/degradation phases.
6. Record MCAP and run metadata.
7. Invoke evaluation pipeline.

---

## 12. Evaluation (Layer 4)

Per-run outputs include:

- mission success/failure
- path/range/energy KPIs
- collision/near-miss counts
- GNSS-denial recovery metrics
- estimator drift metrics

Metadata includes image digests, scenario hash, runtime revisions, and AI model hashes/seeds.

---

## 13. Rendering

- **Primary**: UNav-Sim for perception-grade underwater rendering and camera outputs.
- **Fallback**: PoseidonUE as lightweight ROS visual client if UNav-Sim path is blocked.

Rendering never owns physics or actuator authority.

---

## 14. Interface contracts

Canonical control topics:

- `/auv/thruster_cmd`
- `/auv/fin_cmd`
- `/ssv/thruster_cmd`
- `/ssv/rudder_cmd`

Canonical state/sensor/environment:

- `/auv/state`, `/ssv/state`
- `/auv/sensors/*`, `/ssv/sensors/*`
- `/env/*`

Federation:

- `/sim/auv/clock`
- `/sim/ssv/clock`
- `/scenario/clock`
- `/federation/sync_state`
- `/federation/runtime_health`

---

## 15. Runtime profiles

### Profile A (dev/demo)

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic + DAVE + VRX
- UNav-Sim enabled
- AI enabled

### Profile B (edge/mission)

- Air-gap capable
- Headless operation supported
- Layer 2 remains fully functional without Unreal/AI
- All artifacts pre-bundled offline

---

## 16. Determinism baseline

Release baseline is `ai_mode: off`.

Determinism inputs to pin:

- scenario seed
- DAVE seed
- VRX seed
- federation scheduler seed

---

## 17. Execution plan

### 24-hour vertical slice

1. DAVE publishes `/auv/state`.
2. VRX publishes `/ssv/state`.
3. Federation bridge publishes synchronized `/scenario/clock`.
4. One choke-point scenario executes end-to-end.
5. UNav-Sim renders at least one mission camera stream.
6. MCAP and baseline KPI set are produced.

### 2-week stabilization

- Harden federation failure handling.
- Add determinism regression pack.
- Validate fallback rendering path.

---

## 18. Risks

1. Federation complexity and timing edge cases.
2. DAVE/VRX upstream version drift.
3. UNav-Sim integration drift with UE updates.
4. Deterministic replay drift across dual runtimes.

Mitigations: pin revisions, deterministic scheduler, CI integration gates, maintained PoseidonUE fallback.

---

## 19. Explicit non-goals (MVP)

- Full custom CAD replacement.
- Full CFD-grade hydrodynamics/acoustics.
- Internet-dependent runtime installs.
- Any AI-in-the-loop actuator authority.

---

## 20. Open questions

1. Final ownership split of federation bridge implementation (C++ core vs Python orchestration).
2. Canonical source of truth for shared ocean forcing when DAVE and VRX models diverge.
3. Long-term strategy: remain federated or converge to unified runtime.
