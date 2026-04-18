# POSEIDEN MVP - Open-Source Stack

Companion document to `SYSTEM_DESIGN.md`. Lists every open-source dependency the MVP plans to adopt, what we use it for, what we explicitly chose not to use, and the build-vs-buy rationale.

---

## 1. Adoption principles

1. **Buy the commodity, build the differentiator.** Physics engines, EKFs, behavior trees, sensor plugins, and visualizers are commodity. Scenario engine, nav cascade, GNSS-denial logic, evaluation harness, and autonomy are where we add value.
2. **One authority per concern.** One physics authority (Stonefish). One visual authority (Unreal/UNav-Sim). One nav fusion library (robot_localization). One mission state-machine framework (BehaviorTree.CPP). Multiple simulators running in parallel is a tax we do not pay.
3. **License-compatible and exportable.** Prefer BSD / MIT / Apache-2.0. GPL components are isolated behind process boundaries (ROS 2 nodes) so they do not taint the rest of the stack. No dependency graph we cannot ship as an unclassified platform.
4. **Active maintenance.** Dependencies must have commits in the last 12 months or demonstrate a stable, finished state. No abandoned code in the critical path.
5. **Swap-outable.** Every external dependency sits behind an internal interface so it can be replaced without rewriting downstream code.

---

## 2. The stack by layer

### 2.1 Physics and simulation core

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **Stonefish** | Primary 6-DOF physics for AUV and SSV; buoyancy, drag, thrusters, seabed contact; ROS 2 integration via `stonefish_ros2`. One Stonefish instance runs both vehicles. | Core | BSD |
| **stonefish_ros2** | ROS 2 bridge to Stonefish; scene loading, topic publication, TF. | Core | BSD |
| **ROS 2 Jazzy** | Messaging, services, actions, TF, QoS, DDS discovery. Integration layer. | Core | Apache-2.0 |

Links: <https://github.com/patrykcieslak/stonefish>, <https://github.com/patrykcieslak/stonefish_ros2>, <https://docs.ros.org/en/jazzy/>

### 2.2 Visual rendering

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **Unreal Engine 5.4** | Scenario-review visuals, hero-asset rendering, water surface, lighting, camera cinematics. Consumer of state only; no physics authority. | Core | Custom (Epic EULA - free until $1M revenue) |
| **UNav-Sim** | Underwater visual environment in UE5, vision-based navigation workflows, synthetic camera data for SLAM and perception evaluation. | Core | MIT (check repo) |
| **Unreal Datasmith** | Direct STEP import from SolidWorks for maximum CAD fidelity on hero-asset vehicles. | Core | Included with UE |
| **Unreal Water System** | Surface waves, buoyancy proxy (visual only), shoreline rendering. | Core | Included with UE |

Links: <https://arxiv.org/abs/2310.11927>, <https://dev.epicgames.com/documentation/unreal-engine/water-meshing-system-and-surface-rendering-in-unreal-engine>

### 2.3 Sensor plugins

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **Project DAVE sensor library** | DVL, USBL, multibeam sonar, side-scan sonar, acoustic comms modem plugin references. Adapt for Stonefish or wrap DAVE nodes. Saves weeks of sensor development. | Core | Apache-2.0 |
| **HoloOcean sonar models** | Reference for high-fidelity side-scan, forward-looking, and imaging sonar models if sonar fidelity becomes a differentiator post-MVP. | Tier 2 | MIT |
| **ROS 2 `sensor_msgs`** | Standard sensor message types for tooling compatibility. | Core | Apache-2.0 |

Links: <https://github.com/Field-Robotics-Lab/dave>, <https://byu-holoocean.github.io/holoocean-docs/>

### 2.4 Navigation and state estimation

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **robot_localization** | EKF / UKF sensor fusion for both vehicles. AUV: INS + DVL + USBL + TAN + optional surfaced-GNSS. SSV: GNSS + IMU + speed-log + optional feature-match. Primary nav fusion engine for MVP. | Core | BSD |
| **evo** | Trajectory evaluation (ATE, RPE, alignment). Drop-in for the evaluation pipeline to get standard nav-quality metrics. | Core | GPL-3.0 (used at eval time only, not linked into platform) |
| **GTSAM** | Factor-graph backend for smoothed nav fusion (e.g., out-of-order USBL fixes). Upgrade path, not MVP. | Tier 2 | BSD |
| **Kalibr** | Sensor calibration if we add hardware-in-the-loop later. | Tier 3 | BSD |

Links: <https://github.com/cra-ros-pkg/robot_localization>, <https://github.com/MichaelGrupp/evo>, <https://gtsam.org/>

### 2.5 Autonomy and mission

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **MOOS-IvP** | SSV behavior-based autonomy. Bridged to ROS 2 via a thin adapter. MIT's battle-tested USV autonomy framework. | Core | LGPL / GPL (process-boundary isolation) |
| **BehaviorTree.CPP** | Nav-mode state machines for both vehicles; mission sequencing; phase transitions. Industry-standard, used by Nav2. | Core | MIT |
| **ArduPilot SITL (ArduSub / ArduBoat)** | Optional baseline autopilot for A/B controller comparisons. "Our controller vs. ArduPilot" is a clean evaluation pattern. | Tier 2 | GPL-3.0 (process-isolated) |
| **MAVROS** | ROS 2 bridge to MAVLink autopilots (ArduPilot, PX4). Only needed if we adopt ArduPilot SITL. | Tier 2 | BSD / GPL |

Links: <https://oceanai.mit.edu/moos-ivp/pmwiki/pmwiki.php>, <https://github.com/BehaviorTree/BehaviorTree.CPP>, <https://ardupilot.org/>

### 2.6 Oceanography and environment

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **OpenDrift** | Physics-consistent drift / current field generation for parameterized archetypes. Not used to ingest real-world forecasts; used as an engine behind the scenes for plausible current fields. | Tier 2 | GPL-2.0 (used as offline generator; output is data, not linked) |
| **gsw (Gibbs SeaWater / TEOS-10)** | Sound speed from temperature / salinity / pressure. Drives the acoustic environment and USBL accuracy. | Core | BSD |
| **Fossen MSS (Marine Systems Simulator)** | Canonical SSV hydrodynamic coefficient reference. We borrow published numbers for similar hulls as SSV starting point. | Core | MIT |
| **JONSWAP / Pierson-Moskowitz wave spectrum implementations** | Parameterized wave spectra for sea-state presets. Small Python implementations available in many repos. | Core | Various permissive |
| **arlpy (with Bellhop)** | Acoustic ray-trace propagation. Post-MVP upgrade path for real sound-speed-profile-driven USBL accuracy and transmission-loss curves. | Tier 3 | BSD (Bellhop has usage terms) |
| **VRX (Virtual RobotX)** | Reference only. Borrow WAM-V coefficients and wave plugin math. Do not adopt VRX as a live runtime (it is Gazebo-based; would parallel Stonefish). | Reference | Apache-2.0 |

Links: <https://opendrift.github.io/>, <https://github.com/TEOS-10/GSW-Python>, <https://github.com/cybergalactic/MSS>, <https://github.com/org-arl/arlpy>, <https://github.com/osrf/vrx>

### 2.7 Logging, replay, evaluation

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **rosbag2 with MCAP storage** | Primary recording format. Every scenario run produces an MCAP. | Core | Apache-2.0 |
| **Foxglove Studio** | Primary dashboard and MCAP replay viewer. Scenario review. | Core | MPL-2.0 (free tier sufficient) |
| **PlotJuggler** | Time-series debugging, control-loop tuning, nav-mode transition analysis. | Core | MPL-2.0 |
| **rviz2** | 3D visualization during live runs; TF tree debugging. | Core | BSD |
| **MLflow** | Run tracking across sweeps. Per-seed metrics, comparison across controller versions. Alternative: Weights & Biases (not fully open-source). | Core | Apache-2.0 |

Links: <https://github.com/ros2/rosbag2>, <https://mcap.dev/>, <https://foxglove.dev/>, <https://github.com/facontidavide/PlotJuggler>, <https://mlflow.org/>

### 2.8 CAD pipeline and mesh processing

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **Blender 4.x** | STEP import (via add-on or FreeCAD intermediate), decimation, UV, glTF / OBJ export. Primary mesh-processing host. | Core | GPL-2.0+ (tool, not linked) |
| **FreeCAD** | Optional STEP manipulation path; scriptable with Python. | Core | LGPL |
| **V-HACD** | Convex decomposition for collision meshes. | Core | BSD |
| **trimesh** (Python) | Mesh repair, watertightness checks, inertia tensor computation from meshes (sanity-check against SolidWorks mass properties). | Core | MIT |
| **Open3D** | 3D data processing, point-cloud handling for sonar playback visualization. | Tier 2 | MIT |
| **Capytaine** | Linear potential-flow hydrodynamics (BEM) for proper added-mass computation. Post-MVP upgrade path. | Tier 3 | GPL-3.0 |

Links: <https://www.blender.org/>, <https://www.freecad.org/>, <https://github.com/kmammou/v-hacd>, <https://github.com/mikedh/trimesh>, <https://www.open3d.org/>, <https://github.com/capytaine/capytaine>

### 2.9 Scenario engine and configuration

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **Hydra** (Facebook AI) | Config composition for scenarios: default + archetype + overrides. Clean way to manage the YAML schema hierarchy. | Core | MIT |
| **Pydantic** | Scenario YAML validation against a schema. Fail fast on invalid configs. | Core | MIT |
| **pytest + hypothesis** | Property-based testing for seed determinism; regression tests across scenario files. | Core | MIT / BSD |

Links: <https://hydra.cc/>, <https://docs.pydantic.dev/>, <https://hypothesis.readthedocs.io/>

### 2.10 Infrastructure

| Tool | What we use it for | Tier | License |
| --- | --- | --- | --- |
| **Docker + Docker Compose** | Reproducible dev and demo environments. Essential for "same seed produces same run" across machines. | Core | Apache-2.0 |
| **Nvidia Container Toolkit** | GPU passthrough to containers for Stonefish, Unreal, and GPU-accelerated sensor plugins. | Core | Apache-2.0 |
| **uv** (or Poetry) | Python dependency management. | Core | MIT / Apache-2.0 |
| **GitHub Actions** | CI: build, lint, unit tests, scenario-reproducibility regression. | Core | GitHub terms |
| **pre-commit** | Hooks for formatting, linting, schema validation. | Core | MIT |

Links: <https://www.docker.com/>, <https://github.com/NVIDIA/nvidia-container-toolkit>, <https://github.com/astral-sh/uv>, <https://pre-commit.com/>

---

## 3. Adoption tiers summary

### 3.1 Core (adopt in MVP)

- Stonefish, stonefish_ros2, ROS 2 Jazzy
- Unreal Engine 5.4, UNav-Sim, Datasmith, Unreal Water System
- Project DAVE sensor library
- robot_localization, evo
- MOOS-IvP, BehaviorTree.CPP
- gsw, Fossen MSS coefficients, JONSWAP/PM implementations
- rosbag2 + MCAP, Foxglove Studio, PlotJuggler, rviz2, MLflow
- Blender, FreeCAD, V-HACD, trimesh
- Hydra, Pydantic, pytest + hypothesis
- Docker, Nvidia Container Toolkit, uv, GitHub Actions, pre-commit

### 3.2 Tier 2 (optional for MVP, likely post-MVP)

- HoloOcean sonar models
- GTSAM
- ArduPilot SITL + MAVROS
- OpenDrift (scope: offline current-field generator for archetypes)
- Open3D

### 3.3 Tier 3 (future phases)

- Kalibr
- arlpy + Bellhop (real acoustic propagation)
- Capytaine (proper hydrodynamic added-mass)
- Gazebo underwater vehicles
- Full VRX runtime

---

## 4. What we explicitly do NOT adopt (and why)

| Candidate | Why not | What we do instead |
| --- | --- | --- |
| **BlueTopo** | Per the pivot to parameterized mission environments, real bathymetry ingest is out of scope. Keeps MVP unclass and avoids coverage gaps. | Procedural archetype generator in `world_generator/`. |
| **NOAA chart GIS layers** | Same as above. | Archetype-driven obstacles and shipping lanes. |
| **AWS Open Data pipelines** | Same as above. | Seeded procedural generation. |
| **VRX full runtime** | Gazebo-based; running in parallel to Stonefish doubles the integration surface. | Borrow WAM-V coefficients and wave math as reference; keep Stonefish as physics authority. |
| **Gazebo underwater vehicles** | Overlaps with Stonefish. Two physics stacks is a tax. | Stonefish for both vehicles. |
| **HoloOcean as primary runtime** | Strong sonar, but adopting it means running another UE-based sim in parallel to UNav-Sim. | Reference only; borrow sonar model techniques if needed. |
| **UUV Simulator** | Effectively unmaintained; superseded by Project DAVE. | Project DAVE. |
| **Full CFD (OpenFOAM)** | Enormous compute; not evaluation-relevant for MVP. | Stonefish geometric drag + Fossen coefficients. |
| **Full acoustic propagation (Bellhop/Kraken) in MVP** | Requires real SSP data paths and is slow. | Parameterized acoustic environment; arlpy as post-MVP on-ramp. |
| **HLA / DIS / TENA gateways** | No interop requirement for MVP. | Architectural seam left in telemetry bus for future gateway. |
| **Classified / restricted data paths** | MVP is unclass. | Data-only vehicle configs so classified parameters can swap in later without code changes. |

---

## 5. Build-vs-buy matrix

| Component | Decision | Source |
| --- | --- | --- |
| 6-DOF rigid-body physics | Buy | Stonefish |
| SSV surface dynamics | Buy (coefficients) + configure | Fossen MSS + Stonefish surface vessel |
| AUV hydrodynamics | Buy | Stonefish (geometric drag) |
| Sensor plugins (IMU, DVL, depth, camera, sonar) | Buy / adapt | Project DAVE |
| USBL model | Buy / adapt | Project DAVE |
| Acoustic modem pipe | Build | Trivial range/latency/loss node |
| GNSS mode node (nominal/denied/jammed/spoofed) | Build | Small, specific, our differentiator |
| Nav fusion (EKF/UKF) | Buy | robot_localization |
| Nav-mode state machine | Build on framework | BehaviorTree.CPP |
| Nav cascade (SSV -> USBL -> AUV) | Build | Our differentiator |
| SSV autonomy baseline | Buy | MOOS-IvP (bridged to ROS 2) |
| AUV autonomy | Build | Our differentiator |
| Optional baseline autopilot | Buy | ArduPilot SITL (Tier 2) |
| Mission sequencing | Buy framework | BehaviorTree.CPP |
| Scenario engine | Build | Our differentiator |
| Archetype world generator | Build | Our differentiator |
| Evaluation metrics | Build on library | evo + custom nav-specific metrics |
| Comparison / sweep reports | Build | Our capstone T&E feature |
| Underwater visual scene | Buy | UNav-Sim + Unreal |
| Surface visual scene | Buy | Unreal + Water System |
| CAD to mesh pipeline | Buy + script glue | Blender + V-HACD + trimesh |
| Logging / replay | Buy | rosbag2 + MCAP + Foxglove |
| Run tracking | Buy | MLflow |
| Config management | Buy | Hydra + Pydantic |
| Containerization | Buy | Docker + Nvidia CTK |

---

## 6. License posture

All Core-tier dependencies are permissive (BSD, MIT, Apache-2.0, MPL-2.0) with three intentional exceptions, each isolated behind a process boundary:

- **MOOS-IvP (LGPL / GPL)** - runs as its own process, communicates via a ROS 2 bridge. No linking into the rest of the platform.
- **evo (GPL-3.0)** - used only at evaluation time against MCAP files; produces reports, not runtime code.
- **Blender / FreeCAD (GPL / LGPL)** - tools in the CAD pipeline; outputs are data files, no linking.

This posture supports shipping the platform as an unclassified deliverable and later distributing it to third parties without GPL taint. The internal interfaces to each of the isolated components are narrow enough that they can be swapped for proprietary or permissive alternatives if required.

---

## 7. Critical dependencies risk

The six dependencies where failure would meaningfully disrupt the MVP, ranked:

1. **Stonefish** - physics authority. Mitigation: single point of ownership; contributors responsive; fallback is Gazebo + plugins (3-4 week port).
2. **UNav-Sim / UE5** - underwater visuals. Mitigation: Unreal is stable; UNav-Sim layer is thin enough to replace with custom UE5 work if needed.
3. **Project DAVE** - sensor models. Mitigation: individual sensors can be re-implemented in 1-2 days each.
4. **robot_localization** - nav fusion. Mitigation: very stable package; fallback is hand-rolled EKF (1 week).
5. **MOOS-IvP** - SSV autonomy. Mitigation: BehaviorTree.CPP already in stack; can express SSV behaviors natively if MOOS bridging becomes painful (2-3 weeks).
6. **stonefish_ros2** - ROS 2 bridge. Mitigation: thin wrapper; trivially forkable if upstream stalls.

---

## 8. Update cadence

This document is a living artifact. Expect updates when:

- A new Core-tier dependency is adopted.
- A dependency moves between tiers (Tier 2 promoted to Core, or Core demoted).
- A dependency is replaced or dropped.
- License posture changes for any Core-tier dependency.

Cross-reference: `SYSTEM_DESIGN.md` section 14 (repository layout), section 16 (build plan).
