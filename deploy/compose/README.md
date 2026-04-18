# deploy/compose

Profile A dev-workstation stack per `INFRASTRUCTURE_DESIGN.md` Section 4.1.

## Quickstart

```
cp .env.example .env
docker compose --profile core config --quiet
docker compose --profile core up
```

All services are `busybox` placeholders until real images land. `docker
compose config --quiet` is CI-gated to keep this file always valid.

## Profiles

| Profile | Services | Purpose |
| --- | --- | --- |
| `core` | scenario-engine, sim, nav-*, autonomy-*, mcap-recorder, eval | Mission-essential core. Runs with no AI, no Unreal. |
| `ai` | ai-runtime, eval-ai | Layer 3 runtime AI + Layer 4 LLM. Profile A only. |
| `viz` | unreal, foxglove, dashboard | Visual rendering and live dashboard. |
| `obs` | (reserved) | Prometheus / Grafana / Loki stack, added later. |

## Profile B note

This Compose file is Profile A only. Profile B (edge / mission) deploys via
k3s and the Helm chart under `../../charts/poseidon-platform/`.
