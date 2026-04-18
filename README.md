# POSEIDON MVP

[![CI](https://github.com/Yonatand21/poseidon-mvp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Yonatand21/poseidon-mvp/actions/workflows/ci.yml)

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

```text
poseidon-mvp/
  README.md
  SYSTEM_DESIGN.md
  OPEN_SOURCE_STACK.md
  INFRASTRUCTURE_DESIGN.md
  AGENTS.md
  CONTRIBUTING.md

  poseidon-sim/
    env_service/
    world_generator/
    auv_sim/                # DAVE-side integration (mock today)
    ssv_sim/                # VRX-side integration (mock today)
    coupling/               # federation / time-sync bridge
    sensor_models/
    nav/
    autonomy_auv/
    autonomy_ssv/
    ai/
    scenario_engine/
    evaluation/
    rendering/              # UNav-Sim primary + PoseidonUE fallback

  vehicles/
  scenarios/
  models/
  charts/poseidon-platform/
  deploy/compose/
  deploy/docker/
  tests/
  tools/
  docs/runbooks/
```

---

## Prerequisites

- **Docker Desktop 4.30+** with Buildx (Mac) or **Docker Engine 24+** (Linux)
- **8 CPU / 12 GB RAM / 80 GB disk** allocated to Docker
- **git 2.39+** with `git-lfs`
- **uv 0.5+** (installed by the setup scripts below)
- Optional: **Node.js 20+** if you want to run markdownlint locally

Supported hosts:

- macOS on Apple Silicon (linux/arm64 inside Docker)
- Ubuntu 22.04 / 24.04 (linux/amd64)
- Other Linux distros: dev works; CI is Ubuntu 24.04.

---

## Quickstart

### 1. Clone

```bash
git clone https://github.com/Yonatand21/poseidon-mvp.git
cd poseidon-mvp
```

### 2. Install host toolchain

Pick the script that matches your host. Idempotent - safe to re-run.

```bash
bash tools/setup-mac.sh        # macOS (Apple Silicon or Intel)
# or
bash tools/setup-linux.sh      # Ubuntu / Debian / Fedora / RHEL / WSL2
```

### 3. Repo sanity checks

```bash
helm lint charts/poseidon-platform
docker compose -f deploy/compose/docker-compose.yml config --quiet
uv lock && git diff --exit-code uv.lock
```

### 4. Bring up the federated core

```bash
docker compose -f deploy/compose/docker-compose.yml --profile core up -d --build
```

### 5. Verify topics are live

```bash
docker compose -f deploy/compose/docker-compose.yml exec -T sim-auv \
  bash -lc "source /opt/ros/jazzy/setup.bash && \
            ros2 topic list | egrep '^/auv/state$|^/ssv/state$|^/scenario/clock$'"
```

Expected:

- `/auv/state`
- `/ssv/state`
- `/scenario/clock`

### 6. Run the Tier-1 verification

```bash
bash tools/verify-backbone-t1.sh
```

This builds the base image, bootstraps a deterministic scenario, confirms all federated topics, records an MCAP to `recordings/`, then tears down. Should exit 0 in under 2 minutes on a warm cache.

### 7. Optional - visual profile

```bash
docker compose -f deploy/compose/docker-compose.yml --profile viz up -d
docker compose -f deploy/compose/docker-compose.yml ps foxglove unav-sim-render poseidonue-bridge
```

---

## Active tracks

Parallel workstreams, each self-contained. Pick up any track; the runbook is the contract.

| Track | Goal | Runbook | Touches |
| --- | --- | --- | --- |
| AUV runtime | Replace mock AUV with DAVE on Gazebo Harmonic | [`docs/runbooks/integration-auv-dave.md`](./docs/runbooks/integration-auv-dave.md) | `poseidon-sim/auv_sim/`, `deploy/docker/sim-auv-dave.Dockerfile` |
| SSV runtime | Replace mock SSV with VRX on Gazebo Harmonic | [`docs/runbooks/integration-ssv-vrx.md`](./docs/runbooks/integration-ssv-vrx.md) | `poseidon-sim/ssv_sim/`, `deploy/docker/sim-ssv-vrx.Dockerfile` |
| Tier-2 evaluation | MCAP -> KPI -> Streamlit dashboard chain | [`docs/runbooks/tier-2-evaluation.md`](./docs/runbooks/tier-2-evaluation.md) | `poseidon-sim/evaluation/` |

Branch names: `feat/auv-dave-integration`, `feat/ssv-vrx-integration`, `feat/tier-2-evaluation`. See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

All runtimes must honor [`SYSTEM_DESIGN.md`](./SYSTEM_DESIGN.md) Section 14 (Interface contracts). Validate with:

```bash
python3 tests/integration/test_runtime_contract.py --vehicle both
```

---

## Status

Federated MVP baseline is live on `main` and CI-green on multi-arch builds (linux/amd64 + linux/arm64).

What works today:

1. Dual runtime bring-up (`sim-auv` + `sim-ssv`, mock publishers).
2. Federation bridge publishing `/scenario/clock`, `/federation/runtime_health`, `/federation/sync_state`.
3. Scenario engine emitting deterministic `drop_commit` events.
4. MCAP recording to `recordings/` with full topic coverage.
5. Tier-1 verification script passing end-to-end.

What's next:

1. AUV runtime: mock -> DAVE on Gazebo Harmonic (`feat/auv-dave-integration`).
2. SSV runtime: mock -> VRX on Gazebo Harmonic (`feat/ssv-vrx-integration`).
3. Tier-2: Streamlit KPI dashboard reading MCAPs (`feat/tier-2-evaluation`).

---

## Documentation map

Read in this order:

1. [`SYSTEM_DESIGN.md`](./SYSTEM_DESIGN.md) - architecture and layer contracts.
2. [`OPEN_SOURCE_STACK.md`](./OPEN_SOURCE_STACK.md) - dependency choices and reuse strategy.
3. [`INFRASTRUCTURE_DESIGN.md`](./INFRASTRUCTURE_DESIGN.md) - deployment, security, and operations.
4. [`AGENTS.md`](./AGENTS.md) - hard engineering invariants.
5. [`CONTRIBUTING.md`](./CONTRIBUTING.md) - development workflow, branch conventions, PR checklist.

Runbooks:

- [`docs/runbooks/backbone-verification.md`](./docs/runbooks/backbone-verification.md) - Tier 0-4 verification tiers.
- [`docs/runbooks/dev-setup.md`](./docs/runbooks/dev-setup.md) - Mac / Linux / Windows host setup.
- [`docs/runbooks/cloud-demo-box.md`](./docs/runbooks/cloud-demo-box.md) - Linux + NVIDIA cloud workstation provisioning.
- [`docs/runbooks/integration-auv-dave.md`](./docs/runbooks/integration-auv-dave.md) - AUV runtime track.
- [`docs/runbooks/integration-ssv-vrx.md`](./docs/runbooks/integration-ssv-vrx.md) - SSV runtime track.
- [`docs/runbooks/tier-2-evaluation.md`](./docs/runbooks/tier-2-evaluation.md) - Tier-2 evaluation track.

---

## License

TBD. See `OPEN_SOURCE_STACK.md` Section 6 for license posture and NOTICE obligations.
