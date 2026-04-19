# poseidon-sim-auv-dave
#
# AUV runtime image: DAVE on Gazebo Harmonic + ROS 2 Jazzy.
# Replaces the mock AUV runtime once integration is complete.
#
# Track: AUV runtime. Playbook: docs/runbooks/integration-auv-dave.md
# Contract: SYSTEM_DESIGN.md Section 14 (Interface contracts).
# Layer invariants: AGENTS.md Rule 1.1, 1.5.
#
# Important:
# - This image is a Linux/NVIDIA-targeted placeholder during the prep phase.
# - Do not try to build real DAVE from this file on Mac arm64.
# - Keep mock_auv_runtime.py as the Mac-safe fallback until cloud-box wiring.

ARG POSEIDON_IMAGE_REGISTRY=ghcr.io/yonatand21/poseidon-mvp
ARG POSEIDON_IMAGE_TAG=dev
FROM ${POSEIDON_IMAGE_REGISTRY}/poseidon-base-dev:${POSEIDON_IMAGE_TAG}

LABEL org.opencontainers.image.description="POSEIDON MVP - AUV runtime (DAVE on Gazebo Harmonic)"
LABEL poseidon.runtime="dave"
LABEL poseidon.vehicle="auv"
LABEL poseidon.host_requirement="linux-nvidia"

ARG DEBIAN_FRONTEND=noninteractive
ARG DAVE_REPO=https://github.com/Field-Robotics-Lab/dave.git
ARG DAVE_REF=jazzy
ARG DAVE_VEHICLE=rexrov

USER root

# Gazebo Harmonic is inherited from deploy/docker/base-dev.Dockerfile.
# Keep this file focused on DAVE-specific build/install steps.

# TODO(auv): clone and colcon-build DAVE for ROS 2 Jazzy + Gazebo Harmonic.
# Pin the upstream revision before cloud-box builds are enabled.
# Planned shape:
# RUN git clone --depth 1 --branch ${DAVE_REF} ${DAVE_REPO} /src/dave
# RUN cd /src/dave && git rev-parse HEAD
# RUN mkdir -p /workspace/ws/src && ln -s /src/dave /workspace/ws/src/dave
# RUN bash -lc "source /opt/ros/jazzy/setup.bash && \
#     cd /workspace/ws && \
#     colcon build --merge-install"

# TODO(auv): install one stock DAVE AUV model (RexROV or LAUV).
# Current placeholder vehicle is controlled by:
#   ARG DAVE_VEHICLE=rexrov

# TODO(auv): add any DAVE runtime dependencies that are not already covered
# by the shared base image, but keep this file lean.

USER poseidon
WORKDIR /workspace

# TODO(auv): default to the DAVE launch file once implemented.
# Planned shape:
# CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && \
#      ros2 launch auv_sim auv_dave.launch.py \
#      use_mock_backend:=false \
#      world_name:=dave_ocean_waves.world \
#      vehicle_name:=rexrov"]
CMD ["bash", "-lc", "echo 'sim-auv-dave placeholder - Linux/NVIDIA only, Mac uses mock_auv_runtime.py during prep' && sleep infinity"]
