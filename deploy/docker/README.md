# deploy/docker

Base image Dockerfiles per `INFRASTRUCTURE_DESIGN.md` Section 3.1.

## Image family

```text
poseidon-base-dev          -> Ubuntu 24.04 + ROS 2 Jazzy (Profile A)
poseidon-base-edge         -> Ubuntu 22.04 + ROS 2 Humble (Profile B baseline)
poseidon-base-edge-rhel    -> Rocky 9 + ROS 2 Humble/Jazzy (Profile B, RHEL family)
```

Each application image (`poseidon-sim`, `poseidon-nav`, `poseidon-autonomy`,
`poseidon-scenario-engine`, `poseidon-eval`, ...) builds FROM one of these
bases. Mission-essential core images build against both `dev` and `edge`
bases. Mission-enhancing images (Unreal, web dashboard) build against `dev`
only.

## Invariants

- Digest pinning: production manifests reference by `@sha256:...`, never
  by tag.
- cosign-signed; verified at deploy in Profile B.
- Non-root runtime user.
- Read-only root filesystem compatible.
- No runtime network fetches (apt, pip, model hub).
- SBOM generated per image via syft; stored alongside the image.

Real FROM contents and apt/pip layers land when the first real application
image consumes a base. Keeping bases minimal until then.
