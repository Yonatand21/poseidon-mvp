# unreal-bridge
#
# ROS 2 -> Unreal bridge service. Runs rosbridge_server with a read-only
# topic allowlist.
# See ADR-0001 and the README in this directory.

ARG BASE_IMAGE=ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev
# hadolint ignore=DL3006
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/Yonatand21/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP rosbridge_websocket for UE5"
LABEL poseidon.component="unreal-bridge"

USER root

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-rosbridge-server \
        ros-${ROS_DISTRO}-rosbridge-suite \
        && rm -rf /var/lib/apt/lists/*

USER poseidon
WORKDIR /workspace

EXPOSE 9090

CMD ["ros2", "launch", "/workspace/poseidon-sim/rendering/bridge/bridge.launch.py"]
