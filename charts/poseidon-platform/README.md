# poseidon-platform

Umbrella Helm chart for deploying POSEIDON federated runtime components.

## Usage

```bash
helm lint charts/poseidon-platform
helm install poseidon charts/poseidon-platform -f charts/poseidon-platform/values-dev.yaml
```

## Subcharts

| Chart | Tier | Notes |
| --- | --- | --- |
| `simulation-core` | mission-essential | Includes `sim-auv` (DAVE), `sim-ssv` (VRX), federation bridge, env/nav/autonomy core. |
| `scenario-engine` | mission-essential | Scenario orchestration and run lifecycle. |
| `evaluation` | mission-essential | MCAP recording and KPI processing. |
| `rendering` | mission-enhancing | UNav-Sim path and PoseidonUE fallback bridge. |
| `dashboard` | optional | Web UI and run browsing. |
| `gateway` | optional | API/auth front door for managed deployments. |
| `observability` | optional | Prometheus/Grafana/Loki stack. |

