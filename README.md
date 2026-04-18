# POSEIDON MVP

Software-first maritime test and evaluation platform for coupled AUV + SSV missions in controllable ocean and navigation conditions.

Current architecture baseline:

- AUV runtime: DAVE on Gazebo Harmonic.
- SSV runtime: VRX on Gazebo Harmonic.
- Federation bridge: ROS 2 time-sync and event bridge between runtimes.
- Visual path: UNav-Sim primary / PoseidonUE fallback.
- Deterministic orchestration: scenario-driven, seed-controlled, MCAP recorded.

Canonical terminology used across docs:

- `federation bridge` = the runtime time-sync and event-ordering service in `poseidon-sim/coupling`.
- `dual-runtime ownership` = DAVE owns AUV simulation truth, VRX owns SSV simulation truth.
- `UNav-Sim primary / PoseidonUE fallback` = default visual/perception path and backup path.

---

## What we are building

- Parameterized maritime environments (bathymetry, current, sea state, visibility, acoustic profile).
- GNSS-denied and contested navigation workflows.
- Meshed SSV-to-AUV mission flow with drop handoff.
- Deterministic run/replay with KPI evaluation.
- AI augmentation on top of a classical safety baseline.

---

## Repository layout

```
poseidon-mvp/
  README.md
  SYSTEM_DESIGN.md
  OPEN_SOURCE_STACK.md
  INFRASTRUCTURE_DESIGN.md
  AGENTS.md

  poseidon-sim/
    env_service/
    world_generator/
    auv_sim/                # DAVE-side integration
    ssv_sim/                # VRX-side integration
    coupling/               # federation/time-sync bridge
    sensor_models/
    nav/
    autonomy_auv/
    autonomy_ssv/
    ai/
    scenario_engine/
    evaluation/
    rendering/

  vehicles/
  scenarios/
  models/
  charts/poseidon-platform/
  deploy/compose/
  deploy/docker/
  tests/
```

---

## Quickstart (scaffold phase)

```bash
git clone <repo-url> poseidon-mvp
cd poseidon-mvp

bash tools/setup-mac.sh
# or
bash tools/setup-linux.sh

helm lint charts/poseidon-platform
docker compose -f deploy/compose/docker-compose.yml config --quiet
uv lock --check
```

Bring up core services:

```bash
docker compose -f deploy/compose/docker-compose.yml --profile core up
```

---

## Status

Documentation and scaffolding are aligned to the federated Gazebo architecture. Active implementation tracks:

1. Dual runtime bring-up (`sim-auv` + `sim-ssv`).
2. Federation bridge and synchronized scenario clock.
3. UNav-Sim integration for perception-ready camera streams.
4. Deterministic regression harness for dual-runtime runs.

---

## Federated MVP quick verify

```bash
docker compose -f deploy/compose/docker-compose.yml --profile core up -d --build
docker compose -f deploy/compose/docker-compose.yml exec -T sim-auv bash -lc "source /opt/ros/jazzy/setup.bash && ros2 topic list | egrep '^/auv/state$|^/ssv/state$|^/scenario/clock$'"
bash tools/verify-backbone-t1.sh
```

Expected core topics:

- `/auv/state`
- `/ssv/state`
- `/scenario/clock`

Optional demo visual profile:

```bash
docker compose -f deploy/compose/docker-compose.yml --profile viz up -d
docker compose -f deploy/compose/docker-compose.yml ps foxglove unav-sim-render poseidonue-bridge
```

---

## Documentation map

Read in this order:

1. [`SYSTEM_DESIGN.md`](./SYSTEM_DESIGN.md) - architecture and layer contracts.
2. [`OPEN_SOURCE_STACK.md`](./OPEN_SOURCE_STACK.md) - dependency choices and reuse strategy.
3. [`INFRASTRUCTURE_DESIGN.md`](./INFRASTRUCTURE_DESIGN.md) - deployment, security, and operations.
4. [`AGENTS.md`](./AGENTS.md) - hard engineering invariants.
