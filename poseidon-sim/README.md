# poseidon-sim

Application code for POSEIDON MVP. Layout follows the federated Gazebo architecture in `SYSTEM_DESIGN.md`.

## Layer map

| Directory | Layer | Responsibility |
| --- | --- | --- |
| `env_service/` | 1 | Canonical ocean/environment state service. |
| `world_generator/` | 1 | Procedural archetype generator and runtime projection outputs. |
| `auv_sim/` | 1 | DAVE-side AUV simulation integration and topic adapters. |
| `ssv_sim/` | 1 | VRX-side SSV simulation integration and topic adapters. |
| `sensor_models/` | 1 | Sensor wrappers and normalization for common topic contracts. |
| `coupling/` | 1/2 | Federation bridge: time sync, mission event ordering, runtime health. |
| `nav/` | 2 | Estimation and nav environment degradation nodes. |
| `autonomy_auv/` | 2 | AUV classical autonomy and safety invariants. |
| `autonomy_ssv/` | 2 | SSV classical autonomy and safety invariants. |
| `ai/` | 3 | Advisory perception/planning/risk modules. |
| `scenario_engine/` | orchestration | Scenario schema, launch orchestration, run control. |
| `evaluation/` | 4 | Metrics, reports, dashboards, offline evaluation AI. |
| `rendering/` | visual | UNav-Sim primary / PoseidonUE fallback visual path. |
| `tools/` | dev | CAD/import and archetype tooling utilities. |

## Hard rules

See `AGENTS.md`:

- Layer 2 exclusively owns actuator topics.
- Layer 3 is advisory-only.
- Federation bridge semantics are owned by `coupling/**`.
- Dual-runtime ownership is fixed: DAVE owns AUV truth, VRX owns SSV truth.
- Ground-truth topics are not valid control-loop inputs.
