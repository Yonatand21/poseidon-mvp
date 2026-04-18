# poseidon-base-edge-rhel
#
# Profile B (edge / mission runtime) base image, RHEL family.
# INFRASTRUCTURE_DESIGN.md Section 2.1, Section 3.1, Section 17.4.
#
# Target: Rocky Linux 9 (RHEL 9 compatible) + ROS 2 Humble or Jazzy per
# release validation. Selected per partner environment.
#
# Same constraints as base-edge.Dockerfile.

FROM rockylinux:9
LABEL org.opencontainers.image.source="https://github.com/poseidon-mvp/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP Profile B RHEL-family base - Rocky 9 + ROS 2"
LABEL poseidon.profile="B"
LABEL poseidon.os-family="rhel"
