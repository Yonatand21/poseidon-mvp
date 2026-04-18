# poseidon-base-edge
#
# Profile B (edge / mission runtime) base image, Ubuntu baseline.
# INFRASTRUCTURE_DESIGN.md Section 3.1 and Section 2.1.
# SYSTEM_DESIGN.md Section 17.3 (Edge profile operational invariants).
#
# Target: Ubuntu 22.04 LTS + ROS 2 Humble.
# Constraints (enforced when the real Dockerfile lands):
#   - No runtime apt install. All packages pinned and pre-installed.
#   - No runtime pip install. uv wheelhouse baked in.
#   - Non-root runtime user.
#   - Read-only root filesystem compatible.
#   - Minimum Linux capabilities.
#   - cosign-signed.

FROM ubuntu:22.04
LABEL org.opencontainers.image.source="https://github.com/poseidon-mvp/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP Profile B edge base - Ubuntu 22.04 + ROS 2 Humble"
LABEL poseidon.profile="B"
LABEL poseidon.ros-distro="humble"
