# poseidon-sim

Application code for POSEIDON MVP. Layout follows `SYSTEM_DESIGN.md` Section 15.

## Layer map

| Directory | Layer | Responsibility |
| --- | --- | --- |
| `env_service/` | 1 | Ocean state service (wave, current, wind, SSP, noise). |
| `world_generator/` | 1 | Procedural archetype generator (heightfield, obstacles, traffic, currents). |
| `auv_sim/` | 1 | Stonefish integration for the AUV (plugins, sensor mounts). |
| `ssv_sim/` | 1 | Stonefish integration for the SSV. |
| `sensor_models/` | 1 | Pluggable sensor models (IMU, DVL, depth, sonar, GNSS, compass, radar, camera, USBL, acoustic modem). |
| `coupling/` | 1/2 | Carries / drop handoff state machine and acoustic+RF comms pipe. |
| `nav/` | 2 (and `gnss_env`, `acoustic_env` are 1) | EKF/UKF fusion per vehicle; GNSS and acoustic-env nodes. |
| `autonomy_auv/` | 2 | AUV classical autonomy and safety invariants. |
| `autonomy_ssv/` | 2 | SSV classical autonomy and safety invariants. |
| `ai/` | 3 | Advisory perception, planning, risk, anomaly detection. Advisory only. |
| `scenario_engine/` | orchestration | YAML schema, scene generation, ROS 2 graph launcher, fault injector. |
| `evaluation/` | 4 | Metrics, plots, dashboards, reports, offline Evaluation AI. |
| `rendering/` | visual | Unreal Engine bridge and scene consumers. |
| `tools/` | developer | CAD pipeline scripts, archetype preview utilities. |

## Layer rules

See [AGENTS.md](../AGENTS.md) for the hard rules. In short:

- Only `autonomy_auv/**` and `autonomy_ssv/**` publish actuator topics.
- `ai/**` is advisory. It never publishes actuator topics and is never a
  hard dependency of Layer 2.
- Safety invariants in `autonomy_*/safety_invariants` run unconditionally.
- Ground-truth `/auv/state` and `/ssv/state` are consumed only by `evaluation/`.

## Status

All modules are scaffold-only. Per the 24-hour hackathon sprint plan
(`SYSTEM_DESIGN.md` Section 18.2), first real code lands in a subset of
`env_service/`, `auv_sim/`, `ssv_sim/`, `sensor_models/`, `nav/`,
`autonomy_auv/`, `autonomy_ssv/`, `scenario_engine/`, `evaluation/`,
`rendering/bridge/`, and the choke-point archetype in `world_generator/`.
