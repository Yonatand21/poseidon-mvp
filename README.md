# POSEIDEN MVP

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

## Documentation map

This repo is currently design docs. Three files, read in the order below.

### 1. [`SYSTEM_DESIGN.md`](./SYSTEM_DESIGN.md) - start here

The application design. What the system does, how the layers fit together, what the demo leads with. Read this first.

Key sections:

- **1-3: Goals, capability headlines, top-level architecture.** The pitch and the block diagram.
- **4: Four-layer architecture.** Physics, classical stack, AI augmentation, AI evaluation.
- **5-7: Environment, vehicle CAD, sensors (Layer 1).** What the world and vehicles look like.
- **8-9: Navigation and classical autonomy (Layer 2).** Nav cascade, GNSS-denial behavior, control, failsafes.
- **10: AI augmentation (Layer 3).** Where AI lives and the safety sandbox around it.
- **11: Meshed SSV + AUV with drop handoff.** The mission choreography.
- **12: Scenario engine.** How scenarios are defined, parameterized, and swept.
- **13: Evaluation and metrics (Layer 4).** What we measure and how we score runs.
- **14: Unreal visual layer.** Rendering and hero-asset visuals.
- **15: Repository layout.** Planned code tree for `poseiden-sim/`.
- **16: Interface contracts.** ROS 2 topics, messages, and layer boundaries.
- **17: Platform profiles and edge deployability.** Profile A vs Profile B compatibility matrix.
- **18: Execution plan.** 24-hour hackathon vertical slice, then post-hackathon build-out.
- **19-22: Risk register, non-goals, problem-statement alignment, open questions.**

### 2. [`OPEN_SOURCE_STACK.md`](./OPEN_SOURCE_STACK.md) - what we adopt and why

The build-vs-buy ledger. Every external dependency, what it gives us, and what we deliberately chose not to use.

Key sections:

- **1: Adoption principles.** Buy the commodity, build the differentiator. License rules. Swap-outability.
- **2: The stack by layer.** Physics (Stonefish), visual (Unreal, UNav-Sim), sensors (Project DAVE), nav (robot_localization, GTSAM), autonomy (BehaviorTree.CPP), recording (MCAP), evaluation (evo), orchestration, AI, observability.
- **3: Adoption tiers summary.** Core / Tier 2 / Tier 3 table.
- **4: What we explicitly do NOT adopt.** And the reasons.
- **5: Build-vs-buy matrix.** Per-component decisions.
- **6-8: License posture, critical-dependency risk, update cadence.**

### 3. [`INFRASTRUCTURE_DESIGN.md`](./INFRASTRUCTURE_DESIGN.md) - how we ship and run it

The Linux-native infrastructure, deployment, scaling, security, and compliance contract that keeps dev workstations, air-gapped partner installs, and multi-tenant clusters coherent.

Key sections:

- **1: Audiences and deployment modes.** Runtime profiles x topologies. Design principles.
- **2: Base Linux environment.** OS, kernel, GPU, host packages.
- **3: Container strategy.** The `poseiden-*` image family, signing, SBOMs, offline bundles.
- **4: Orchestration.** Docker Compose, k3s, Kubernetes. Helm chart layout under `poseiden-platform/`.
- **5-7: Data, compute, scaling.** MCAP storage, PostgreSQL, MinIO, GPU scheduling, sweep workers.
- **8-9: Networking and security.** DDS, air-gap, zero-trust, cosign, secrets, auth.
- **10: Observability.** Prometheus, Grafana, Loki, OpenTelemetry.
- **11: CI/CD.** Release gating, regression suite, signed releases.
- **12: Multi-tenancy.** Namespace isolation, quotas, per-tenant version pinning.
- **13: Compliance roadmap.** National-security and commercial export posture.
- **14-15: Backups, DR, ops and support model.**
- **16: Reference topologies.** Dev workstation, partner single-node appliance, multi-tenant cluster.
- **17-19: Non-goals, roadmap, cross-references.**

---

## Suggested reading order

- **New to the project:** `SYSTEM_DESIGN.md` sections 1-4, then 18 (execution plan).
- **Engineer about to write code:** `SYSTEM_DESIGN.md` 15-16 (repo layout + interface contracts), then `OPEN_SOURCE_STACK.md` 2 (stack by layer).
- **Deploying or operating:** `INFRASTRUCTURE_DESIGN.md` 1, 3, 4, 16.
- **Security / compliance review:** `INFRASTRUCTURE_DESIGN.md` 9, 12, 13.
- **Edge / air-gapped partner work:** `SYSTEM_DESIGN.md` 17, then `INFRASTRUCTURE_DESIGN.md` 1-4 and 16.2.

---

## Status

Design phase. No code in this repo yet. The first implementation milestone is the 24-hour hackathon vertical slice described in `SYSTEM_DESIGN.md` Section 18.2.
