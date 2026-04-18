# POSEIDON MVP - Open-Source Stack (Federated Gazebo Pivot)

Companion to `SYSTEM_DESIGN.md`. This document captures the dependency strategy for the DAVE + VRX + UNav-Sim architecture.

## 1. Adoption principles

1. Reuse mature maritime open-source stacks first.
2. Keep authority boundaries explicit (AUV runtime, SSV runtime, federation bridge).
3. Keep ROS interfaces stable even when upstream implementations differ.
4. Keep all mission-essential dependencies pin-able and edge deployable offline.

## 2. Core stack

| Area | Dependencies |
| --- | --- |
| AUV runtime | Gazebo Harmonic + DAVE |
| SSV runtime | Gazebo Harmonic + VRX |
| Federation | Internal bridge in `poseidon-sim/coupling` |
| Visual/perception | UNav-Sim + UE5 (primary), PoseidonUE (fallback) |
| Nav/control | robot_localization + internal Layer 2 autonomy |
| Evaluation | rosbag2 + MCAP + evaluation pipeline |
| Infrastructure | Docker/Compose, Helm, k3s/Kubernetes, NVIDIA Container Toolkit |

## 3. Reuse scope

### 3.1 DAVE reuse

- AUV model and underwater sensor plugin baselines.
- Underwater world/environment plugin patterns.
- Gazebo + ROS launch integration scaffolding.

### 3.2 VRX reuse

- WAM-V and SSV hydrodynamic/propulsion references.
- Surface-vessel world and task patterns.
- Sea-state and wave configuration baselines.

### 3.3 UNav-Sim reuse

- Underwater visual and perception rendering.
- Camera stream generation for segmentation, SLAM, and fusion workflows.

## 4. Explicit non-adoptions for this pivot

- Stonefish as primary runtime authority.
- Full custom vehicle-from-scratch modeling during MVP sprint.
- Runtime dependency downloads from public internet.
- Unreal-owned physics or control authority.

## 5. Key risks and mitigations

1. DAVE/VRX upstream drift on Gazebo/ROS versions.
   - Mitigation: pin revisions, container digests, and CI compatibility checks.
2. Federation time-sync and deterministic event ordering complexity.
   - Mitigation: deterministic scheduler + dual-runtime regression tests.
3. UNav-Sim integration drift with UE updates.
   - Mitigation: keep PoseidonUE fallback path maintained and contract-compatible.

## 6. License posture

Primary mission runtime dependencies are permissive (Apache-2.0 / MIT / BSD). Any GPL/LGPL usage remains process-isolated where applicable.

Release rule: every imported upstream dependency must include pinned revision and license metadata in release artifacts.
