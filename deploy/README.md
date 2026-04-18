# deploy

Deployment assets.

## Layout

| Dir | Purpose |
| --- | --- |
| `compose/` | Profile A dev-workstation Docker Compose stack. |
| `docker/` | Base image Dockerfiles (dev, edge, edge-rhel). |

Helm charts for k3s and multi-tenant Kubernetes live at the repo root under
[`../charts/`](../charts/) per `INFRASTRUCTURE_DESIGN.md` Section 4.4.

## Topologies

| Topology | Path | Use |
| --- | --- | --- |
| Dev workstation | `compose/docker-compose.yml` | Internal engineering, one-command bring-up. |
| Partner on-prem | `../charts/poseidon-platform/` with `values-onprem.yaml` | Single-node or 3-node k3s, air-gap capable. |
| Multi-tenant cluster | `../charts/poseidon-platform/` with `values-multitenant.yaml` | Upstream Kubernetes, hardened. |
