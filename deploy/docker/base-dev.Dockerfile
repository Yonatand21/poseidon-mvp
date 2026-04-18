# poseidon-base-dev
#
# Profile A development base image.
# INFRASTRUCTURE_DESIGN.md Section 3.1 (Image families),
# SYSTEM_DESIGN.md Section 17.4 (Platform compatibility matrix).
#
# Target: Ubuntu 24.04 LTS + ROS 2 Jazzy.
#
# This is a scaffold stub. The real Dockerfile lands when the first
# application image builds against it. Do not add apt/pip layers until
# the first real consumer exists; bloating the base wastes CI cycles.

FROM ubuntu:24.04
LABEL org.opencontainers.image.source="https://github.com/poseidon-mvp/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP Profile A base - Ubuntu 24.04 + ROS 2 Jazzy"
LABEL poseidon.profile="A"
LABEL poseidon.ros-distro="jazzy"
