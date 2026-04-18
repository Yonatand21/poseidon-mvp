# poseidon-sim
#
# Mission-essential core simulator image (Layer 1). FROM poseidon-base-dev.
# Installs Stonefish from source plus stonefish_ros2 on amd64.
# On arm64 (Mac M4 dev), Stonefish is skipped - only the ARM64 Linux build
# does not exist upstream today - and a mock publisher is used instead so
# the full ROS 2 graph still boots on the Mac for bridge / scenario-engine
# / evaluation development.
#
# OPEN_SOURCE_STACK.md Section 2.1 (Stonefish, stonefish_ros2).
# SYSTEM_DESIGN.md Section 4.1 (Layer 1 physics) and Section 18.2.2
# (24-hour hackathon sprint scope).
#
# Build:
#   docker buildx build \
#     --platform linux/amd64 \
#     -f deploy/docker/poseidon-sim.Dockerfile \
#     -t ghcr.io/yonatand21/poseidon-mvp/poseidon-sim:dev \
#     .

ARG BASE_IMAGE=ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev
# hadolint ignore=DL3006
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/Yonatand21/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP simulator (Stonefish + stonefish_ros2) on Profile A base"
LABEL poseidon.layer="1"
LABEL poseidon.component="sim"

ARG TARGETARCH
ARG DEBIAN_FRONTEND=noninteractive
ARG STONEFISH_TAG=1.4.0
ARG STONEFISH_ROS2_BRANCH=main

USER root

# Stonefish build + runtime deps (Section 6.4 of OPEN_SOURCE_STACK.md and
# upstream README). Consolidated into one layer; no-install-recommends to
# keep image size down.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglm-dev \
        libsdl2-dev \
        libopenal-dev \
        libfreetype6-dev \
        libxmu-dev \
        libxi-dev \
        libgl1-mesa-dev \
        libglew-dev \
        && rm -rf /var/lib/apt/lists/*

# Stonefish + stonefish_ros2 build (amd64 only). On arm64 a no-op stub is
# installed instead; the compose file routes arm64 sim to the mock package.
# hadolint ignore=DL3003
RUN set -eux; \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        mkdir -p /opt/poseidon/build && cd /opt/poseidon/build; \
        git clone --depth 1 --branch "${STONEFISH_TAG}" https://github.com/patrykcieslak/stonefish.git; \
        cmake -S stonefish -B stonefish-build -G Ninja -DCMAKE_BUILD_TYPE=Release; \
        cmake --build stonefish-build --parallel; \
        cmake --install stonefish-build; \
        ldconfig; \
    else \
        echo "Stonefish skipped on ${TARGETARCH}; mock sim via poseidon_sim_mock." > /opt/poseidon/stonefish-skipped.txt; \
    fi

# stonefish_ros2 colcon workspace (amd64). The ROS 2 overlay ends up at
# /workspace/install/setup.bash which is sourced by the entrypoint.
# hadolint ignore=SC1091
RUN set -eux; \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        mkdir -p /workspace/src && cd /workspace/src; \
        git clone --depth 1 --branch "${STONEFISH_ROS2_BRANCH}" https://github.com/patrykcieslak/stonefish_ros2.git; \
        cd /workspace; \
        . /opt/ros/${ROS_DISTRO}/setup.sh; \
        colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release; \
        chown -R poseidon:poseidon /workspace; \
    fi

# Install the ARM64 mock sim as an editable Python package. The package
# source lives in the repo under poseidon-sim/auv_sim/mock and is bind-
# mounted at runtime via the compose file. At image build time we only
# register the entrypoint; the code itself is live-mounted from the host.
# This avoids a rebuild on every code change during dev.

USER poseidon
WORKDIR /workspace
