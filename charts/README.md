# charts

Helm charts for POSEIDON MVP k3s and Kubernetes deployments.

**Design reference:** `INFRASTRUCTURE_DESIGN.md` Section 4.4.

## Layout

- `poseidon-platform/` - umbrella chart. See its [README](poseidon-platform/README.md).

## CI

`helm lint charts/poseidon-platform` runs in `.github/workflows/ci.yml`
on every PR. Keep the chart lint-clean.
