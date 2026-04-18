# POSEIDON MVP

A software-based maritime test and evaluation environment for AUV (Autonomous Underwater Vehicle) and SSV (Surface Support Vessel) performance across controllable ocean and navigation conditions - including GNSS-denied and contested environments - with classical control, AI augmentation, and AI-driven evaluation.

The headline capability is **repeatable virtual test-and-evaluation under controllable ocean and navigation conditions, with AI augmentation layered on top of a deterministic classical core**.

---

## What we are building

- **Parameterized maritime environments.** Bathymetry archetypes (open water, continental shelf, littoral, choke point, harbor approach), sea state 1-6, currents, visibility tiers, acoustic-nav infrastructure, sound speed profiles.
- **GNSS-denied and contested operations.** Full nav-cascade modeling: SSV GNSS degradation propagates to AUV via USBL; AUV falls back to INS + DVL + TAN + acoustic aiding.
- **Meshed AUV + SSV missions.** One scenario clock, shared environment, SSV-to-AUV drop handoff, acoustic comms pipe.
- **Deterministic, repeatable trials.** Seeded scenarios, MCAP recordings, deterministic replay.
- **Four-layer architecture.**
  1. Stonefish physics + ROS 2 (vehicles, sensors, ocean).
  2. Classical navigation, control, safety (robot_localization, BehaviorTree.CPP).
  3. AI augmentation - advisory only, never in the actuator path (perception, planning, risk prediction, anomaly detection).
  4. AI-driven evaluation - metrics, failure clustering, LLM-generated performance summaries.
- **Two runtime profiles.** Profile A (Ubuntu 24.04 + ROS 2 Jazzy, dev/demo with Unreal + AI) and Profile B (Ubuntu 22.04 / RHEL 9 + ROS 2 Humble, edge/mission, air-gap capable).
- **Three deployment topologies.** Dev workstation (Docker Compose), partner on-prem appliance (single-node k3s), multi-tenant Kubernetes cluster. Same images and Helm charts across all three.

---

## Repository layout

```
poseidon-mvp/
  README.md                  entry point (this file)
  SYSTEM_DESIGN.md           application design (start here)
  OPEN_SOURCE_STACK.md       build-vs-buy ledger
  INFRASTRUCTURE_DESIGN.md   deployment, scaling, security
  AGENTS.md                  hard architectural rules (layer separation, determinism)
  CONTRIBUTING.md            workflow and PR checklist
  pyproject.toml             uv-managed Python project (zero deps for now)

  poseidon-sim/              application code (Layer 1-4)
    env_service/             Layer 1 - ocean state
    world_generator/         Layer 1 - procedural archetypes
    auv_sim/ ssv_sim/        Layer 1 - Stonefish integration
    coupling/                Layer 1/2 - carry, drop, comms pipe
    sensor_models/           Layer 1 - IMU, DVL, sonar, GNSS, USBL, etc.
    nav/                     Layer 2 (+ Layer 1 env nodes)
    autonomy_auv/            Layer 2 - AUV classical autonomy
    autonomy_ssv/            Layer 2 - SSV classical autonomy
    ai/                      Layer 3 - advisory AI (perception, planner, risk, anomaly)
    scenario_engine/         orchestration
    evaluation/              Layer 4 - metrics, plots, reports, offline AI
    rendering/               Unreal bridge and project
    tools/                   CAD pipeline, archetype preview

  vehicles/                  CAD artifacts (STEP, meshes, configs) via Git LFS
  scenarios/                 user-facing scenario YAML library
  models/                    pinned AI model artifacts + hashes

  charts/poseidon-platform/  Helm umbrella chart + 7 subcharts (k3s + k8s)
  deploy/compose/            Profile A Docker Compose stack
  deploy/docker/             base image Dockerfiles (dev, edge, edge-rhel)

  tests/determinism/         release-gate deterministic regression suite
  tests/integration/         ROS 2 topic + scenario-engine integration tests
  tests/unit/                pure-Python unit tests

  tools/                     repo-wide dev tools (layer-permission lint, etc.)
  docs/architecture/         ADRs
  docs/runbooks/             operational runbooks

  .github/                   CI, CODEOWNERS, PR template
```

---

## Quickstart

Dev environment is cross-platform. Host tooling differs by OS; the runtime
is always Ubuntu inside Docker. Full walkthrough for Mac / Linux / Windows
(WSL2) in [`docs/runbooks/dev-setup.md`](./docs/runbooks/dev-setup.md).

```bash
git clone <repo-url> poseidon-mvp
cd poseidon-mvp

# One-shot, idempotent toolchain installer. Pick the one matching your host:
bash tools/setup-mac.sh       # macOS (Apple Silicon or Intel)
bash tools/setup-linux.sh     # Ubuntu / Debian / Fedora / RHEL / WSL2 Ubuntu

# Validate the repo is healthy (the setup scripts run these automatically).
helm lint charts/poseidon-platform
docker compose -f deploy/compose/docker-compose.yml config --quiet
uv lock --check

# Bring up the dev stack (busybox placeholders until components land).
docker compose -f deploy/compose/docker-compose.yml --profile core up
```

Prerequisites you install manually before the script:

- **Docker Desktop** (Mac / Windows) or **Docker Engine** will be installed
  by the Linux script.
- **Unreal Engine 5.4** (only if you work on the rendering track): Epic
  Games Launcher, <https://www.unrealengine.com/en-US/download>.
- **Windows users:** install Docker Desktop with WSL2 backend, enable WSL2
  integration for an Ubuntu-22.04 distro, then run `tools/setup-linux.sh`
  from inside WSL2. See the runbook Windows section.

Target: new engineer runs the hero scenario within 30 minutes of cloning,
per `SYSTEM_DESIGN.md` Section 18.2.1.

---

## Status

Scaffolding phase. The repository structure, CI, and infrastructure skeletons are in place; application code is placeholder-only.

Next milestone is the 24-hour hackathon vertical slice described in `SYSTEM_DESIGN.md` Section 18.2: one vehicle pair, one choke-point archetype, one GNSS-denial event, MCAP recording, Unreal replay, and 3-5 KPIs.

---

## Documentation map

Three design docs, read in the order below.

### 1. [`SYSTEM_DESIGN.md`](./SYSTEM_DESIGN.md) - start here

The application design. What the system does, how the layers fit together, what the demo leads with.

Key sections:

- **1-3:** Goals, capability headlines, top-level architecture.
- **4:** Four-layer architecture and the safety model.
- **5-7:** Environment, vehicle CAD, sensors (Layer 1).
- **8-9:** Navigation and classical autonomy (Layer 2).
- **10:** AI augmentation (Layer 3).
- **11:** Meshed SSV + AUV with drop handoff.
- **12:** Scenario engine.
- **13:** Evaluation and metrics (Layer 4).
- **14:** Unreal visual layer.
- **15:** Repository layout.
- **16:** Interface contracts (ROS 2 topics).
- **17:** Platform profiles and edge deployability.
- **18:** Execution plan (24-hour sprint + 10-week roadmap).
- **19-22:** Risk register, non-goals, problem-statement alignment, open questions.

### 2. [`OPEN_SOURCE_STACK.md`](./OPEN_SOURCE_STACK.md) - what we adopt and why

The build-vs-buy ledger. Every external dependency, what it gives us, and what we deliberately chose not to use.

### 3. [`INFRASTRUCTURE_DESIGN.md`](./INFRASTRUCTURE_DESIGN.md) - how we ship and run it

The Linux-native infrastructure, deployment, scaling, security, and compliance contract that keeps dev workstations, air-gapped partner installs, and multi-tenant clusters coherent.

---

## Suggested reading order

- **New to the project:** `SYSTEM_DESIGN.md` Sections 1-4, then 18 (execution plan).
- **Engineer about to write code:** `SYSTEM_DESIGN.md` 15-16 (repo layout + interface contracts), `OPEN_SOURCE_STACK.md` 2, and `AGENTS.md`.
- **Deploying or operating:** `INFRASTRUCTURE_DESIGN.md` 1, 3, 4, 16.
- **Security / compliance review:** `INFRASTRUCTURE_DESIGN.md` 9, 12, 13.
- **Edge / air-gapped partner work:** `SYSTEM_DESIGN.md` 17, `INFRASTRUCTURE_DESIGN.md` 1-4 and 16.2.
- **Contributing:** `CONTRIBUTING.md`, `AGENTS.md`.
