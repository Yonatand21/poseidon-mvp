# POSEIDON MVP - Infrastructure and Scaling Design

Companion document to `SYSTEM_DESIGN.md` and `OPEN_SOURCE_STACK.md`. This doc covers the Linux-native infrastructure, deployment modes, scaling architecture, security posture, and compliance roadmap required to deliver the platform to national-security and commercial partners.

The platform is not an internal tool. It is a product that will run in three very different deployment contexts: individual engineer workstations, partner-owned air-gapped servers, and multi-tenant clusters. This document is the contract that keeps those three contexts coherent.

---

## 1. Audiences and deployment modes

Deployment is defined along two orthogonal axes: **runtime profile** (per `SYSTEM_DESIGN.md` Section 17) and **topology**. Both matter; they are not the same question.

### 1.1 Runtime profiles (from `SYSTEM_DESIGN.md` Section 17)

| Profile | OS baseline | ROS 2 | Unreal | Layer 3 AI | Layer 4 AI | Offline install |
| --- | --- | --- | --- | --- | --- | --- |
| **A - Development / Demo** | Ubuntu 24.04 | Jazzy | Enabled | Enabled | Enabled | Optional |
| **B - Edge / Mission** | Ubuntu 22.04 LTS or RHEL/Rocky 9 | Humble (or validated Jazzy subset) | Disabled by default | Optional, signed packages | Optional, offline only | Required |

Profile A is the development track. Profile B is the mission track. The infrastructure described in this document supports both without forking the codebase.

### 1.2 Topologies

| Topology | Typical profile | Audience | Orchestration | Connectivity | Lifecycle |
| --- | --- | --- | --- | --- | --- |
| **Dev workstation** | Profile A | Internal engineers, partner engineers during evaluation | Docker Compose | Online | Rolling; latest main |
| **Partner on-prem** | Profile B | Single national-security or commercial partner operating their own infra | Single-node k3s or 3-node k3s cluster, air-gap capable | Air-gapped, periodic offline sync | Quarterly signed releases |
| **Multi-tenant cluster** | Profile A or B per tenant | Multiple partners on shared infra (SaaS or government-shared) | Kubernetes with namespace isolation | Online, hardened | Continuous delivery with per-tenant version pinning |

Topology and profile are decoupled: a multi-tenant cluster can run Profile B for a national-security tenant and Profile A for a commercial tenant on the same cluster, with per-namespace policy enforcement.

### 1.3 Design principles

- **The application is topology-agnostic.** The same code, images, and Helm charts deploy in all three topologies; values files differ.
- **The application is profile-aware.** Mission-essential images build against both profiles; mission-enhancing images are Profile-A only.
- **Classical core is always functional.** A Profile B deployment with all enhancements stripped still executes scenarios, records MCAP, and produces metrics.
- **No release is edge-supported until it passes the deterministic regression suite on Profile B.** This is a release-gate, not a nice-to-have.

---

## 2. Base Linux environment

### 2.1 Operating system

OS support is profile-aware per `SYSTEM_DESIGN.md` Section 17 (Platform profiles and edge deployability). Development and edge targets are intentionally different.

- **Profile A - Development / Demo. Ubuntu 24.04 LTS (Noble Numbat)** with ROS 2 Jazzy is the primary development target. Chosen for newest driver support, latest middleware features, and long-term support through 2029.
- **Profile B - Edge / Mission Runtime. Ubuntu 22.04 LTS** with ROS 2 Humble is the default edge baseline, based on stronger plugin and simulator compatibility at the time of release. A validated Jazzy subset is acceptable only after full compatibility testing on the target host.
- **RHEL 9 / Rocky 9** is a supported edge host family for partner environments requiring RHEL-family infrastructure. Containerization insulates the application from the host distribution, but host-level kernel modules, GPU drivers, and security baselines differ.
- **No Windows, no macOS for production.** Dev workstations on those platforms run via Docker Desktop / Linux VM.
- **Release gating.** No release is declared edge-supported until it passes the deterministic regression suite on the target edge baseline (Ubuntu 22.04 or RHEL 9 as appropriate). The compatibility matrix in `SYSTEM_DESIGN.md` Section 17.4 is updated per release.

### 2.2 Kernel and host requirements

- Linux kernel >= 6.5 for current NVIDIA driver + CUDA stack and modern io_uring support.
- `vm.max_map_count >= 262144` for Stonefish + Unreal memory mapping.
- `net.core.rmem_max` and `net.core.wmem_max` tuned for DDS high-throughput (recommend 25 MB each).
- Ethernet jumbo frames (MTU 9000) on dedicated sim networks for multi-node deployments.
- Real-time kernel (`PREEMPT_RT`) not required for MVP but planned for future hardware-in-the-loop deployments.

### 2.3 GPU and compute

- **NVIDIA GPUs required** for Unreal rendering, camera/sonar sensor simulation, and Layer 3 AI inference.
- Minimum: RTX 4070-class (12 GB VRAM) for Unreal + AI inference on a single node.
- Recommended: RTX 4090 / L40S / H100 for multi-vehicle runs with AI active.
- **NVIDIA Container Toolkit** for GPU passthrough to containers.
- **CUDA 12.4+** as the baseline.
- CPU: 16+ cores recommended; Stonefish + ROS 2 + Unreal + sim workers benefit meaningfully from core count.
- RAM: 64 GB minimum for multi-tenant, 32 GB acceptable for dev workstation.
- Storage: NVMe SSD for MCAP write throughput; 1 TB+ for sweep studies.

### 2.4 Required host packages

Minimum host packages (everything else is inside containers):

- Docker 24+ or Podman 5+
- docker-compose-plugin
- NVIDIA drivers and Container Toolkit
- `git`, `git-lfs` (for large binary CAD artifacts)
- `openssh-server` for remote dev
- `systemd-journald` for container log shipping

---

## 3. Container strategy

Containers are the primary unit of distribution. Every application component ships as a signed OCI image.

### 3.1 Image families

Two base families are maintained in parallel, aligned to the two runtime profiles:

```
poseidon-base-dev                 # Ubuntu 24.04 + ROS 2 Jazzy        (Profile A)
poseidon-base-edge                # Ubuntu 22.04 + ROS 2 Humble        (Profile B, baseline)
poseidon-base-edge-rhel           # RHEL/Rocky 9 + ROS 2 Humble/Jazzy (Profile B, RHEL)

(each base ->)
 +-- poseidon-sim                 # Stonefish + physics + sensor plugins (mission-essential core)
 +-- poseidon-nav                 # robot_localization + nav stacks     (mission-essential core)
 +-- poseidon-autonomy            # classical autonomy (Layer 2)         (mission-essential core)
 +-- poseidon-scenario-engine     # orchestrator                         (mission-essential core)
 +-- poseidon-eval                # metrics + report generation          (mission-essential core)
 +-- poseidon-ai-runtime          # Layer 3 inference                    (mission-enhancing, optional)
 +-- poseidon-eval-ai             # Layer 4 LLM summarization            (mission-enhancing, optional)
 +-- poseidon-unreal              # UE5 headless render / bridge         (mission-enhancing, dev/demo only)
 +-- poseidon-dashboard           # web UI                               (mission-enhancing, optional)
 +-- poseidon-gateway             # API gateway / auth front-door        (multi-tenant only)
```

The mission-essential core tags (`poseidon-sim`, `poseidon-nav`, `poseidon-autonomy`, `poseidon-scenario-engine`, `poseidon-eval`) build against **both** `poseidon-base-dev` and `poseidon-base-edge`. Mission-enhancing images may build against `poseidon-base-dev` only.

Principles:

- **Multi-stage builds.** Build-time deps (compilers, dev headers) stripped from runtime images.
- **Minimum attack surface.** No shells, no package managers, no SSH in production images. Alpine-free for glibc compat with CUDA.
- **Digest pinning.** All base images referenced by digest (`@sha256:...`), not tag, in production manifests. Every `apt install` pins a version; every `pip install` uses a lockfile. No unpinned `:latest` tags anywhere in production.
- **Offline-first for edge.** Every runtime dependency, AI model, and package required for Profile B operation is available from an offline release bundle. No production edge component may require runtime downloads from public package indices, model hubs, or license servers.
- **Image signing with cosign.** Every image signed and verified at deploy time. Signature verification is mandatory in Profile B.
- **SBOMs generated per image** via `syft` and published alongside the image. Edge release bundles include the full SBOM set.
- **CVE scanning** via `grype` or `trivy` in CI; zero high-severity CVEs in released images.
- **Non-root runtime.** Images run as non-root users where practical; read-only root filesystems are the Profile B default.
- **Minimal capabilities.** Explicit Linux capability set per image; no `--privileged` containers in production; GPU access via the NVIDIA runtime only.

### 3.2 Image registry

- **Public builds**: GitHub Container Registry (ghcr.io) or AWS ECR Public.
- **Partner on-prem**: images delivered as signed tarballs for air-gapped import, OR the partner runs an internal Harbor / JFrog Artifactory instance that we push to.
- **Multi-tenant cluster**: private registry (Harbor recommended on-prem, ECR/GCR in cloud).

---

## 4. Orchestration

Orchestration scales with deployment mode.

### 4.1 Dev workstation - Docker Compose

Single `docker-compose.yml` brings up the full stack on a dev laptop. Volumes mount the source repo so edits are immediate. GPU passthrough via `deploy.resources.reservations.devices`.

```
services:
  stonefish:
  ros2-bridge:
  autonomy-auv:
  autonomy-ssv:
  scenario-engine:
  mcap-recorder:
  foxglove:
  unreal:        # optional, off by default (heavy)
  dashboard:     # optional
```

One-command bring-up: `docker compose up`. Target: a new engineer runs a hero scenario within 30 minutes of cloning.

### 4.2 Partner on-prem - k3s

k3s (lightweight Kubernetes) on one to three nodes. Rationale:

- Same Helm charts as the multi-tenant cluster; no separate deployment surface to maintain.
- Runs air-gapped once images are loaded.
- Handles service restarts, health checks, GPU scheduling.
- Small enough to run on a single appliance-class server.

Reference topology for partner on-prem:

- **Single-node appliance**: one 64-core workstation with 2x GPU. k3s server runs everything. Suitable for small teams.
- **Three-node cluster**: one control-plane node + two GPU worker nodes. Separates orchestration from compute. Suitable for partner mission centers running 10+ concurrent sweep workers.

### 4.3 Multi-tenant cluster - Kubernetes

Full Kubernetes (upstream, EKS, GKE, AKS, or on-prem). Used for:

- Our hosted SaaS (if/when we offer it).
- Government-shared environments where multiple agencies share a cluster.

Capabilities:

- Namespace-per-tenant isolation.
- Resource quotas per tenant.
- Network policies restricting cross-tenant traffic.
- GPU scheduling via NVIDIA GPU Operator.
- Horizontal pod autoscaling for scenario sweep workers.

### 4.4 Helm charts

All three modes use the same set of Helm charts, parameterized by mode:

```
charts/
  poseidon-platform/              # umbrella chart
    charts/
      simulation-core/
      scenario-engine/
      evaluation/
      rendering/
      dashboard/
      gateway/
      observability/
  values-dev.yaml
  values-onprem.yaml
  values-multitenant.yaml
```

One set of charts, three value files. The chart logic branches on mode for auth (local vs. SSO), storage (local vs. S3), and ingress (none vs. hardened).

---

## 5. Data architecture

Data is stratified by durability, size, and access pattern.

### 5.1 Data classes

| Class | Examples | Storage | Retention |
| --- | --- | --- | --- |
| Scenario configs | YAML files | Git + object storage | Forever (versioned) |
| Vehicle / environment artifacts | CAD STEPs, meshes, heightfields | Object storage via Git LFS or direct S3 | Forever (versioned) |
| AI models | ONNX / pickle weight files | Object storage + MLflow model registry | Forever (versioned) |
| Telemetry | MCAP files | Object storage, tiered | Hot 30 days, warm 1 year, cold 7 years |
| Run metadata | Run ID, seed, config hash, metrics | PostgreSQL | Forever |
| Metrics aggregates | Per-run metrics, sweep statistics | PostgreSQL + Parquet exports | Forever |
| User sessions | Auth state | Redis | Short-lived |
| Build artifacts | Container images, Helm charts | OCI registry | Per retention policy |

### 5.2 Storage backends

- **Object storage**: MinIO on-prem (S3-compatible). Commercial cloud: AWS S3 / Azure Blob / GCS / GovCloud equivalents. Single S3 API abstraction across all modes.
- **Relational**: PostgreSQL 16+. Used for run metadata, metrics, user identity (when not delegated to SSO).
- **Cache / queue**: Redis 7+. Used for job queue state and session cache.
- **Model registry**: MLflow backed by PostgreSQL + S3-compatible storage.
- **Time-series (optional)**: VictoriaMetrics or Prometheus for infrastructure metrics. Application metrics (per-run KPIs) live in PostgreSQL because they are queried relationally, not as time series.

### 5.3 MCAP storage tiering

Telemetry is the largest data class and drives storage cost.

- **Hot tier** (NVMe, local object storage): last 30 days. Accessible in milliseconds for replay.
- **Warm tier** (spinning disk object storage, standard S3): 30 days - 1 year. Accessible in seconds.
- **Cold tier** (S3 Glacier / Azure Archive / tape): 1-7 years. Accessible in hours. Retention driven by regulatory requirements.

Automatic lifecycle policies move files between tiers. Metrics aggregates always stay hot (small).

### 5.4 Versioning policy

- Scenario configs: semantic versioned, compatibility matrix published.
- AI models: versioned in MLflow with full lineage (training data, code, hyperparameters).
- Platform releases: semantic versioning (`MAJOR.MINOR.PATCH`).
- Every MCAP records the full version stack it was produced by (platform version, model hashes, scenario hash). Reproducibility is auditable.

---

## 6. Compute architecture

The compute design supports two operating modes that match the two platform profiles in `SYSTEM_DESIGN.md` Section 17: a feature-rich mode with Unreal and AI active, and a headless classical-only mode that remains fully functional on reduced hardware.

### 6.1 Operating modes

**Feature-rich mode (Profile A and well-resourced Profile B).**
- Stonefish + sensor plugins + nav + autonomy + Layer 3 AI + Unreal (if enabled).
- Latency-sensitive; pinned pods on dedicated nodes with GPU and CPU reservations.
- GPU required for Unreal and AI inference.

**Headless classical-only mode (Profile B baseline).**
- Stonefish + sensor plugins + nav + classical autonomy + MCAP recorder + metrics pipeline only.
- No Unreal, no Layer 3 AI, no Layer 4 AI.
- Runs on reduced hardware. GPU recommended for higher-fidelity sensor models; **baseline regression capability remains available in CPU-only reduced-fidelity mode** if rendering and GPU-accelerated sensors are disabled.
- This is the mode defense and edge partners deploy by default. It is the baseline mission runtime.

**Invariant.** The simulation core supports a headless classical-only mode that does not require Unreal or Layer 3 AI. Baseline T&E outputs (scenario execution, ground-truth logging, classical metrics, MCAP recording) must remain valid in this mode for every release.

### 6.2 Real-time simulation node

One or more nodes run the synchronous simulation loop. In feature-rich mode the loop includes Unreal live view; in headless mode Unreal is absent entirely. Both modes share the same simulation, nav, and autonomy images.

### 6.3 Scenario sweep workers

For Monte Carlo and sweep studies, scenarios run embarrassingly in parallel. Sweep workers are stateless pods that:

1. Pull a scenario config from the queue (Redis).
2. Launch an isolated simulation graph (mode per scenario config).
3. Record MCAP to object storage.
4. Insert run metadata and metrics into PostgreSQL.
5. Terminate.

Horizontal autoscaling is driven by queue depth. 100 scenarios can run in 100 workers in parallel given enough compute; the scheduler is GPU-aware via the NVIDIA GPU Operator and assigns headless scenarios preferentially to CPU-only workers when available.

### 6.4 Evaluation and report workers

Layer 4 evaluation (log mining, failure clustering, LLM summarization) runs as a separate pool of workers. These are CPU-heavy but not GPU-required except for LLM inference. They consume MCAPs from object storage and produce reports back to object storage. In Profile B (edge) deployments, Layer 4 runs offline with local models only; no external LLM API calls are permitted.

### 6.5 Job scheduler

Internal service, not Kubernetes itself. Responsibilities:

- Accept sweep job requests (from CLI, web UI, or API).
- Expand sweep definitions into individual scenario configs.
- Enqueue scenarios in Redis.
- Track job status.
- Emit job-complete events.

Scheduler is stateless and horizontally scalable.

### 6.6 Minimum deployable kit

For defense and edge partners asking "what is the smallest thing I can deploy?":

- One Linux host (Ubuntu 22.04 or RHEL/Rocky 9).
- One NVIDIA GPU (recommended) **or** CPU-only for reduced-fidelity regression.
- Local NVMe object storage (MinIO single-node).
- Local PostgreSQL instance.
- Local Redis instance.
- Signed OCI bundle installed offline.
- CLI operator interface on the host.
- Foxglove replay on a separate analyst workstation (optional).

In this configuration the platform delivers complete core T&E outputs: scenario execution, recording, metrics, reports. Missing relative to a full deployment: Unreal visualization quality and Layer 3/4 AI. That is explicitly acceptable as the edge baseline.

---

## 7. Scaling dimensions

The platform scales along four dimensions, each with distinct engineering implications.

### 7.1 Vertical (simulation fidelity per run)

More GPU / more CPU -> higher sensor resolution, more vehicles in one scene, better physics rate. Addressed by hardware choice and pod resource reservations. Upper bound: one scenario stays within one node, because DDS and simulation clock coherence across nodes is expensive.

### 7.2 Horizontal (parallel scenario sweeps)

More nodes -> more scenarios running concurrently. Linear scaling up to thousands of scenarios, because each scenario is independent. Bounded by GPU fleet size and object storage write throughput.

### 7.3 Multi-tenant (concurrent partners)

More tenants -> more namespaces, more quotas, more isolation. Limited by control-plane capacity and operational burden, not by application code. Target capacity: 50+ active tenants on a single cluster with reasonable quotas.

### 7.4 Data retention

More runs -> more MCAP. Linear growth. Addressed by tiering (Section 5.3) and by aggressive deduplication of ground-truth bathymetry and asset artifacts across runs.

---

## 8. Networking

### 8.1 Intra-simulation (DDS)

ROS 2 uses DDS for messaging. Within one simulation pod / node:

- DDS discovery confined to a **dedicated DDS domain per run** so concurrent runs on the same node do not cross-talk.
- ROS 2 QoS profiles pinned per topic, especially for high-rate state and image streams.
- Multicast disabled on shared cluster networks; unicast discovery with explicit peer lists.

### 8.2 Inter-service (within cluster)

- Service mesh optional for MVP. For multi-tenant we adopt Istio or Linkerd for:
  - mTLS between services
  - Per-tenant network policies
  - Traffic observability
- Otherwise plain Kubernetes Services with NetworkPolicies enforcing namespace isolation.

### 8.3 External (ingress)

- **API gateway** front-doors all external access: authentication, rate limiting, audit logging, request signing.
- **Dashboard** behind the gateway.
- **Object storage** via presigned URLs, not directly exposed.
- **DDS never exposed externally.** Ever.

### 8.4 Air-gapped mode

**Air-gapped mode is a first-class supported deployment profile, not a degraded afterthought.** All operational workflows required for scenario execution, replay, reporting, and audit export must be possible without internet connectivity.

Platform guarantees in air-gapped mode:

- Image bundle import (signed tarballs or OCI layout directories).
- Offline Helm chart install.
- Offline AI model import with signature verification.
- Offline scenario import and export.
- Offline license verification; keys are cryptographically signed and validated without any network callback.
- Local auth (Keycloak shipped in the bundle) or partner IdP federation over local network only.
- Local object storage, PostgreSQL, Redis, observability, and replay - all first-class.
- **No telemetry home. Ever.** The platform does not initiate outbound connections from any component in air-gapped mode.

Required release artifacts to qualify a release as edge-supported and air-gap-installable:

- Signed image bundle containing every dependency for Profile B.
- Signed Helm charts.
- Signed AI model artifacts with version manifest.
- Signed scenario libraries and regression packs.
- Offline installation guide with checksum verification procedure.
- Deterministic regression suite executable by the partner against their installed bundle.

Periodic sync (if permitted by partner policy):

- Sneakernet bundles for image and model updates.
- One-way data diodes for audit log exfil to the vendor (with explicit partner authorization).
- All transfers signed and verified end-to-end.

Explicit prohibitions for Profile B:

- No runtime `apt install`, `pip install`, or model download.
- No calls to public package indices, model hubs, or cloud APIs.
- No telemetry submission to the vendor without explicit partner opt-in and written authorization.
- No online license checks. Ever.

---

## 9. Security posture

### 9.1 Identity and authentication

Pluggable identity provider:

- **Dev mode**: local user file, no auth for obvious reasons.
- **Partner on-prem**: OIDC via Keycloak (shipped with the platform) or SAML/OIDC to the partner's existing IdP (Active Directory Federation, Okta, PingFederate).
- **Multi-tenant**: OIDC per tenant; tenant-scoped tokens.

Zero-trust model: every service-to-service call authenticated, authorized, and logged. No implicit network trust.

### 9.2 Authorization

Role-based access control (RBAC) at the application layer:

- `viewer` - read runs, replays, reports.
- `operator` - submit scenarios, review results.
- `author` - create and edit scenario libraries, vehicle configs, AI models.
- `admin` - manage users and tenant configuration.
- `platform_admin` - superuser, infrastructure-level.

Per-tenant role scope in multi-tenant mode.

### 9.3 Secrets management

- **Vault (HashiCorp) recommended** for all non-trivial deployments. Handles database credentials, S3 keys, model-signing keys, LLM API keys.
- **Kubernetes Secrets** acceptable for dev and small on-prem deployments, but always encrypted at rest (KMS-backed).
- **No secrets in images.** Ever. Enforced by CI scanning.

### 9.4 Data classification and handling

- All data inside the platform is treated as **at least CUI-eligible**. Logging, backups, and exports preserve classification markings.
- Scenario configs, CAD artifacts, and AI models may be controlled. The platform supports per-artifact classification metadata and enforces it at access time.
- For classified deployments (IL5+, SAP, etc.), the platform runs inside the partner's accredited enclave. We do not operate classified environments; partners do, using our platform as a GOTS/COTS application.

### 9.5 Export control (ITAR / EAR)

- The platform software itself is unclassified and export-controlled only to the extent that its open-source components are (most are ECCN EAR99).
- **Vehicle configs, sensor parameters, and AI models can be ITAR-controlled.** These are data, not code, and live in partner-controlled storage. The platform treats them as opaque.
- Architecture explicitly supports this separation: code ships unclass; ITAR-controlled parameters load at runtime from partner-controlled sources.

### 9.6 Supply chain security

- **Every image signed with cosign.** Signature verified at deploy.
- **SBOMs published** alongside every image.
- **SLSA Level 3** build provenance target for platform releases.
- **CVE scanning** blocking release on high-severity findings.
- **Dependency pinning** with Renovate or Dependabot for controlled updates.
- **FIPS 140-3 crypto** mode available for partners that require it (via FIPS-validated base images and OpenSSL 3 FIPS module).

### 9.7 Audit logging

- Every authenticated action logged with actor, timestamp, resource, and outcome.
- Every scenario submission, data export, and configuration change logged.
- Logs shipped to partner's SIEM via syslog / Splunk HEC / CEF as appropriate.
- Logs are tamper-evident (append-only object storage with versioning, or partner-managed WORM).

### 9.8 Hardened runtime posture (edge / mission)

For Profile B (edge / mission) deployments, the following runtime hardening applies unconditionally. These are not aspirations; a release is not declared edge-supported unless they are in place.

**Container and workload posture:**
- Non-root containers where practical; explicit `runAsNonRoot: true` in pod specs.
- Read-only root filesystem (`readOnlyRootFilesystem: true`).
- Minimal Linux capabilities per container; all caps dropped by default, explicit allowlist per service.
- No `--privileged` containers; GPU access via the NVIDIA runtime only.
- SELinux or AppArmor profiles shipped with every mission-essential component.
- Seccomp default profile applied; custom profiles for workloads with tighter syscall requirements.

**Host hardening:**
- STIG-aligned host hardening supported and documented; partner applies per their accreditation baseline.
- Host package inventory pinned; no unattended upgrades in operational mode.
- Kernel hardening flags (`lockdown`, module-signing enforcement) supported on partner hosts.

**Signed artifact verification:**
- Signature verification enforced at install time (bundle signature) and at runtime (image signature via cosign).
- FIPS 140-3 crypto path available via FIPS-validated base images and OpenSSL 3 FIPS module for partners that require it.
- DDS-Security / SROS2 policy bundles enforced per release; topic-level access control mirrors the Layer 1/2/3 ROS 2 permission policy in `SYSTEM_DESIGN.md` Section 16.

**Interface minimization:**
- Administrative interfaces (web admin consoles, unauthenticated diagnostic endpoints) removable or disable-by-default in operational mode.
- Only explicitly documented service ports exposed; all others firewalled by NetworkPolicy or host firewall.
- SSH to host optional and policy-controlled; many partners disable entirely in operational state.

**Operator accountability:**
- Operator actions fully audit-logged with actor identity, source host, and command executed.
- Privileged-operation actions require re-authentication (step-up auth).
- Package provenance and SBOM bundles shipped with each release; partners can verify against their own baseline.

**Python boundary.**
- Python is used for scenario orchestration, evaluation, and AI inference only.
- Control loops, timing-sensitive simulation bridges, and critical sensor pipelines remain in C++ or hardened compiled components.
- Python process failures cannot take Layer 2 control offline; Layer 2 runs in a separate process with its own supervisor.

---

## 10. Observability

### 10.1 Application logs

- Structured JSON logs from every service.
- Stdout/stderr collected by the container runtime.
- Aggregated via Loki (on-prem default) or the partner's existing log stack (Splunk, ELK).

### 10.2 Infrastructure metrics

- Prometheus for metrics collection.
- Grafana for dashboards.
- Exporters for node, GPU (DCGM), PostgreSQL, Redis, and MinIO.

### 10.3 Application metrics

- Run-level metrics in PostgreSQL (Section 5.2).
- Queryable via the dashboard and via a REST API.
- Exported as Parquet for external analytics.

### 10.4 Tracing

- OpenTelemetry instrumentation across services.
- Traces shipped to Jaeger or Tempo.
- Particularly useful for diagnosing sweep-worker latency and DDS-graph startup times.

### 10.5 Alerts

- Prometheus Alertmanager -> partner's paging system.
- Default alerts: pod crashloops, GPU saturation, queue backlog, failed scenario runs above threshold, disk pressure, auth failures spike.

---

## 11. CI/CD

### 11.1 Pipeline stages

```
commit -> lint -> unit tests -> build images -> SBOM + scan -> sign -> push ->
                                                                        |
                                        integration tests on ephemeral cluster
                                                                        |
                                              release tag -> chart publish -> deploy
```

- **Lint**: Python (ruff), C++ (clang-tidy), YAML (yamllint), shell (shellcheck), dockerfiles (hadolint).
- **Unit tests**: pytest + gtest + deterministic-scenario regression tests.
- **Build**: multi-arch where practical (amd64 primary, arm64 for dev workstations).
- **Scan**: grype/trivy; block on high CVE.
- **Sign**: cosign with keyless or key-based signing.
- **Integration**: Kind cluster spun up per PR; a canary scenario runs end-to-end.
- **Release**: tag-driven; produces image set + Helm chart + release notes + SBOM bundle.

### 11.2 Environments

- `dev`: every commit.
- `staging`: release candidates, merged to `main`.
- `partner-preview`: optional, on request, specific tag per partner.
- `production`: tagged releases only.

### 11.3 Release cadence

- Hotfix: as needed.
- Minor: monthly.
- Major: quarterly.
- Partner on-prem deployments receive quarterly signed bundles; partners decide when to apply.

---

## 12. Multi-tenancy

### 12.1 Isolation primitives

- **Kubernetes namespace per tenant.** Resources cannot cross namespace without explicit network policy allowance.
- **Per-tenant database**: schema-per-tenant in shared PostgreSQL for small deployments; database-per-tenant for hardened deployments.
- **Per-tenant bucket / prefix** in object storage with distinct IAM roles.
- **Per-tenant AI model registry** in MLflow with isolated model paths.
- **Per-tenant resource quotas** (CPU, memory, GPU, storage).
- **Per-tenant rate limits** at the API gateway.

### 12.2 Data sovereignty

Each tenant's data remains in their namespace and their bucket. The platform never cross-queries tenants. Aggregate analytics across tenants (for our use, e.g., platform health) anonymizes and strips all tenant-identifying data.

### 12.3 Licensing and telemetry

- License keys signed by the vendor, installed per tenant.
- Keys encode: enabled features, user seats, scenario-run ceiling, expiration.
- **Air-gapped deployments**: license enforcement is local-only; keys are cryptographically signed and offline-verified.
- **Online deployments**: optional usage telemetry (opt-in) for support, billing, and product telemetry. Telemetry is **scenario-counts and feature usage only**, never customer data, never MCAP content, never model weights.

### 12.4 Per-tenant customization

- Each tenant can bring their own vehicle configs, sensor models, AI models, and scenario libraries. These live in the tenant's namespace and are invisible to other tenants.
- Platform upgrades must preserve tenant data. Every release includes forward-compatibility tests against prior-release tenant data.
- Tenants can pin platform versions; forcing upgrade requires 90-day notice.

---

## 13. Compliance roadmap

Target compliance postures by partner type.

| Posture | Partner type | Target by |
| --- | --- | --- |
| **SOC 2 Type II** | Commercial | Month 12 post-GA |
| **FedRAMP Moderate** | US federal civil / non-classified defense | Month 18 |
| **FedRAMP High** | US federal sensitive | Month 24 |
| **DoD IL5** | DoD classified up to Secret | Month 30, via partner enclave |
| **NIST SP 800-171** | DoD CUI contractors | Month 12 |
| **CMMC Level 2** | DoD supply-chain partners | Month 15 |
| **ITAR compliance posture** | All USG partners | At GA (architecture supports; formal posture at GA) |
| **ISO 27001** | International commercial | Month 18 |

Controls are implemented incrementally; the architecture in this document is designed to meet the strictest of these without rework. Specifically, the zero-trust service model (Section 9), container signing and SBOM generation (Section 3 / 9.6), audit logging (Section 9.7), and data classification (Section 9.4) are baseline from day one.

---

## 14. Backups and disaster recovery

### 14.1 What is backed up

- PostgreSQL: continuous WAL archiving + nightly base backups.
- Object storage: cross-region replication or equivalent on-prem (bucket versioning + off-appliance snapshots).
- Configuration (Helm values, secrets in Vault): daily backups.
- Scenario and vehicle artifact libraries: Git + object storage, inherently versioned.

### 14.2 Recovery objectives

| Mode | RTO | RPO |
| --- | --- | --- |
| Dev workstation | N/A | N/A |
| Partner on-prem | 4 hours | 1 hour |
| Multi-tenant | 1 hour | 5 minutes |

### 14.3 Drills

- Quarterly restore test for multi-tenant.
- Annual restore test for partner on-prem (contract-driven).
- Every release includes a data migration rehearsal against a prior-release snapshot.

---

## 15. Operations and support model

### 15.1 Release artifacts per version

- Container images (signed)
- Helm charts (signed)
- SBOM bundle
- Release notes with breaking-change callouts
- Migration scripts if DB schema changes
- Upgrade guide
- Rollback guide

### 15.2 Support tiers

- **Community / dev** - GitHub issues, best-effort.
- **Standard partner** - ticketing + business-hours response.
- **Premium partner** - 24/7 on-call + quarterly on-site.
- **National security / mission-critical** - embedded engineer + incident response retainer.

### 15.3 Telemetry and customer success

- Opt-in operational telemetry (license status, error rates, feature usage) for online partners.
- Proactive alerts to partner ops on detected health regressions (if opted in).
- Air-gapped partners receive no telemetry; support is ticket-driven with partner-submitted diagnostics bundles.

---

## 16. Reference topologies

### 16.1 Dev workstation

```
Ubuntu 24.04 laptop, RTX 4070, 32 GB RAM, 1 TB NVMe
-------------------------------------------------
  docker compose:
    stonefish + nav + autonomy + scenario-engine
    mcap-recorder -> local ./mcap/
    foxglove -> localhost:8765
    [optional] unreal, dashboard
```

### 16.2 Partner single-node appliance

```
One 64-core workstation, 2x RTX 4090, 256 GB RAM, 8 TB NVMe + 50 TB HDD
-----------------------------------------------------------------------
  k3s server (single node):
    namespace: poseidon
      simulation-core (multi-replica for sweeps)
      scenario-engine
      evaluation
      rendering (unreal headless)
      dashboard
      gateway (TLS termination, local OIDC via Keycloak)
      observability (prometheus + grafana + loki)
  MinIO (local disk-backed)
  PostgreSQL (single instance)
  Redis (single instance)
  Vault (single instance, sealed until operator unlocks)
  Air-gapped. No internet.
```

### 16.3 Multi-tenant cluster

```
Kubernetes cluster, cloud or on-prem
-------------------------------------
  Control plane: 3 nodes, HA
  Worker pools:
    compute-general: N nodes (16-core each)
    compute-gpu-inference: M nodes (1x L40S each)
    compute-gpu-render: K nodes (1x RTX 4090 or L40S)
    storage: P nodes (MinIO cluster, erasure-coded)

  Shared services:
    Istio service mesh (mTLS, policy)
    Harbor registry
    PostgreSQL HA cluster
    Redis cluster
    Vault HA cluster
    MLflow
    Prometheus + Grafana + Loki + Tempo
    Keycloak (or federated IdP)

  Per-tenant:
    namespace: tenant-<id>
      platform services, tenant-scoped
    database: schema or dedicated instance
    bucket: tenant-<id>-*
    network policies: egress-only to platform services
```

---

## 17. What this architecture is not

Explicit non-goals to keep scope honest:

- **Not a multi-cloud abstraction.** The platform runs on Kubernetes. Kubernetes runs on many clouds and on-prem. We do not build cross-cloud orchestration.
- **Not a high-availability simulation runtime.** A simulation that crashes mid-run is lost; we do not checkpoint live simulations. Recovery is at the job level (re-run the scenario), not at the tick level.
- **Not a data lake.** MCAP archives are not analytics primitives. Export to Parquet + the partner's existing data platform for cross-cutting analytics.
- **Not a general-purpose ML platform.** MLflow is used for our Layer 3 / Layer 4 models, not as a shared training platform for partner ML work.
- **Not an identity provider.** We integrate with partner IdPs; we do not replace them.
- **Not forcing the dev stack onto the mission runtime.** Profile A (Ubuntu 24.04 + Jazzy + Unreal + AI) is the dev track. Profile B (conservative baseline, headless, AI-removable) is the mission track. Do not let release cadence conflate them.

---

## 18. Roadmap

| Phase | Timeframe | Infrastructure milestone |
| --- | --- | --- |
| **Hackathon sprint** | T+24h | Dev workstation mode only; `docker compose up` works |
| **Internal MVP** | Week 4 | Dev workstation polished; CI/CD pipeline basic; image signing |
| **Full platform MVP** | Week 10 | Helm charts draft; single-node k3s reference deployment |
| **First partner on-prem** | Month 4 | Air-gap bundles; Keycloak integration; SBOM + cosign in production |
| **SOC 2 Type II** | Month 12 | Full audit logging, access reviews, backup drills |
| **Multi-tenant GA** | Month 15 | Namespace-per-tenant, quotas, Istio mTLS, license enforcement |
| **FedRAMP Moderate** | Month 18 | Controls documented, continuous monitoring, ATO package |
| **FedRAMP High / IL5** | Month 24-30 | Classified-enclave deployment pattern, FIPS crypto, supply chain attestation |

---

## 19. Cross-references

- `SYSTEM_DESIGN.md` - architecture, capabilities, layered design, scenario engine, evaluation.
- `OPEN_SOURCE_STACK.md` - dependency inventory, build-vs-buy, license posture.

This document is the operational contract that turns the architecture in `SYSTEM_DESIGN.md` into a product that can be shipped to multiple partners under multiple compliance postures without rework.
