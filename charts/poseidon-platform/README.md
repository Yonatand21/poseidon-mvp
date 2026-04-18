# poseidon-platform

Umbrella Helm chart for POSEIDON MVP. Deploys the full platform to k3s
(partner on-prem) or upstream Kubernetes (multi-tenant).

**Design reference:** `INFRASTRUCTURE_DESIGN.md` Section 4 (Orchestration),
Section 4.4 (Helm charts).

## Usage

```
helm lint charts/poseidon-platform

# Profile A, dev on k3s
helm install poseidon charts/poseidon-platform -f charts/poseidon-platform/values-dev.yaml

# Profile B, partner on-prem (air-gap capable)
helm install poseidon charts/poseidon-platform -f charts/poseidon-platform/values-onprem.yaml

# Multi-tenant Kubernetes
helm install poseidon charts/poseidon-platform -f charts/poseidon-platform/values-multitenant.yaml
```

## Subcharts

| Chart | Tier | Enabled in | Notes |
| --- | --- | --- | --- |
| `simulation-core` | mission-essential | always | Stonefish, sensor plugins, Layer 1 and 2 nodes. |
| `scenario-engine` | mission-essential | always | Orchestrator. |
| `evaluation` | mission-essential | always | Metrics pipeline + Foxglove / MCAP storage. |
| `rendering` | mission-enhancing | Profile A | UE5 headless render + bridge. |
| `dashboard` | mission-enhancing | dev + multi-tenant | Web UI. |
| `gateway` | multi-tenant | multi-tenant | API gateway, auth front-door. |
| `observability` | mission-enhancing | on-prem + multi-tenant | Prometheus, Grafana, Loki, OTel. |

All subcharts ship at `version: 0.0.0` and contain only a `Chart.yaml` +
placeholder `values.yaml` until real templates land.
