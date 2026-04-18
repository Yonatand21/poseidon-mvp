# POSEIDON MVP - Infrastructure Design (Federated Gazebo Runtime)

Companion to `SYSTEM_DESIGN.md` and `OPEN_SOURCE_STACK.md`. This document defines how the dual-runtime simulation stack is packaged, deployed, secured, and operated across dev, on-prem, and multi-tenant environments.

Canonical terminology:

- `federation bridge` = time-sync and deterministic event-ordering service between runtimes.
- `dual-runtime ownership` = DAVE owns AUV truth, VRX owns SSV truth.
- `UNav-Sim primary / PoseidonUE fallback` = default visual/perception path with maintained backup.

---

## 1. Deployment modes

### 1.1 Runtime profiles

| Profile | Target | Core components | Optional components |
| --- | --- | --- | --- |
| A (dev/demo) | Workstations and internal clusters | ROS 2 Jazzy, Gazebo Harmonic, DAVE, VRX, federation bridge, Layer 2, MCAP recorder | UNav-Sim, PoseidonUE fallback, Layer 3/4 AI |
| B (edge/mission) | Air-gapped partner infra | Same mission-essential core as A, headless allowed | Visual and AI layers optional/off by default |

### 1.2 Topologies

- Dev workstation: Docker Compose.
- Partner on-prem: single-node or small k3s cluster.
- Multi-tenant: Kubernetes with namespace isolation.

---

## 2. Core runtime composition

Mission-essential containers/services:

1. `sim-auv` (Gazebo Harmonic + DAVE world/plugins).
2. `sim-ssv` (Gazebo Harmonic + VRX world/plugins).
3. `federation-bridge` (clock sync, event order, runtime health).
4. `env-service` (canonical environment topics).
5. `scenario-engine` (run orchestration).
6. Layer 2 nav/autonomy services.
7. `mcap-recorder` + evaluation worker.

Mission-enhancing services:

- `unav-sim-render` (primary visual/perception).
- `poseidonue-bridge` (fallback visual path).
- Layer 3 AI advisory workers.
- Layer 4 AI report workers.

---

## 3. Container and image strategy

### 3.1 Image families

```text
poseidon-base-jazzy
  |- poseidon-sim-auv      (Gazebo + DAVE)
  |- poseidon-sim-ssv      (Gazebo + VRX)
  |- poseidon-federation
  |- poseidon-scenario
  |- poseidon-nav
  |- poseidon-autonomy
  |- poseidon-eval
  |- poseidon-unav         (optional)
  |- poseidon-poseidonue   (fallback optional)
  |- poseidon-ai-runtime   (optional)
```

### 3.2 Build rules

- Pin base images by digest.
- Lock apt/pip dependencies.
- Generate SBOM and sign every runtime image.
- Block release on high-severity CVEs.
- No runtime package installs in Profile B.

---

## 4. Orchestration patterns

### 4.1 Compose (dev)

Single compose stack with separate services for `sim-auv` and `sim-ssv`.

Minimum healthy startup sequence:

1. `env-service`
2. `sim-auv`, `sim-ssv`
3. `federation-bridge`
4. nav/autonomy
5. recorder/evaluation
6. visual/AI optional

### 4.2 k3s / Kubernetes

- Each scenario run receives a unique DDS domain and run ID namespace.
- Federation bridge receives liveness probes from both runtimes.
- Scenario runs are treated as batch jobs for sweeps.

---

## 5. Data architecture

### 5.1 Data classes

| Class | Store | Notes |
| --- | --- | --- |
| Scenario configs | Git + object store | Versioned YAML |
| World artifacts | Object store | DAVE/VRX/UNav projections |
| MCAP telemetry | Object store with lifecycle tiers | Canonical replay artifact |
| Run metadata and KPIs | PostgreSQL | Indexed by run ID and seed |
| AI models | Model registry + object store | Hash-pinned |

### 5.2 Determinism metadata

Every run persists:

- scenario hash
- AUV runtime image digest
- SSV runtime image digest
- federation image digest
- DAVE and VRX source revisions
- AI model hashes and seeds (if enabled)

---

## 6. Federation operations contract

This is the key infrastructure delta from single-runtime designs.

### 6.1 Time synchronization

- Inputs: `/sim/auv/clock`, `/sim/ssv/clock`.
- Output: `/scenario/clock`.
- Policy: deterministic scheduler with bounded drift threshold.

### 6.2 Event consistency

- Mission-critical events (drop commit, phase transitions, hard faults) are sequenced by federation bridge.
- Bridge emits signed run-local event log for post-run audit.

### 6.3 Failure handling

- If one runtime is unhealthy, bridge emits degraded mode.
- Layer 2 safety nodes transition to safe-state logic.
- Scenario engine marks run as partial/degraded with reason code.

---

## 7. Networking

- DDS traffic stays internal to the run namespace/domain.
- `sim-auv`, `sim-ssv`, and federation bridge communicate over private network only.
- External ingress is limited to API/dashboard endpoints.
- DDS and rosbridge are never internet-exposed.

---

## 8. Security posture

### 8.1 Identity and auth

- OIDC for managed deployments.
- Local/offline auth for air-gapped installs.

### 8.2 Secrets

- Vault preferred; encrypted k8s secrets acceptable for dev.
- No secrets baked into images.

### 8.3 Supply chain controls

- Cosign image signatures.
- SBOM bundle per release.
- CVE gating and dependency pinning.

### 8.4 Air-gap guarantees

- Offline install bundle includes all images, models, and charts.
- No outbound license checks.
- No outbound telemetry in Profile B unless partner explicitly enables one-way export.

---

## 9. Observability

- Structured JSON logs per service.
- Federation-specific dashboards:
  - clock drift
  - event queue lag
  - runtime health status
- Prometheus + Grafana + alerting baseline.
- MCAP and event-log correlation for incident analysis.

---

## 10. CI/CD

Pipeline stages:

1. Lint and unit tests.
2. Build and scan images.
3. Sign images and generate SBOM.
4. Integration run with both simulation runtimes + federation bridge.
5. Determinism regression for `ai_mode: off`.
6. Release bundle generation.

Release is blocked if dual-runtime integration or determinism checks fail.

---

## 11. Multi-tenant model

- Namespace per tenant.
- Quotas for CPU/GPU/storage.
- Tenant-isolated object prefixes and database schemas.
- Per-tenant version pinning for controlled upgrades.

---

## 12. Backup and DR

Back up:

- PostgreSQL metadata.
- object store (MCAP + artifacts).
- Helm values and secrets snapshots.

Targets:

- On-prem RTO 4h / RPO 1h.
- Multi-tenant RTO 1h / RPO 5m.

---

## 13. Minimum deployable kit

For partner edge deployments:

- 1 Linux host (or 3-node small cluster).
- GPU optional for headless classical mode, recommended for visual/perception.
- Local object storage + PostgreSQL + Redis.
- Offline signed bundle import tooling.

This kit must run mission-essential dual-runtime simulation without internet connectivity.

---

## 14. Non-goals

- Live checkpoint/restore at simulation tick granularity.
- External DDS exposure.
- Runtime downloads from public package indexes.
- Treating visual/perception services as safety-critical dependencies.

---

## 15. Cross-references

- `SYSTEM_DESIGN.md` for architecture and layer contracts.
- `OPEN_SOURCE_STACK.md` for dependency rationale.
