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

USER root

# TODO(auv): install Gazebo Harmonic via the gazebosim apt repository.
# Reference: https://gazebosim.org/docs/harmonic/install_ubuntu
# This should land first in deploy/docker/base-dev.Dockerfile so both
# sim-auv-dave and sim-ssv-vrx share the layer. Keep this file lean.

# TODO(auv): clone and colcon-build DAVE for ROS 2 Jazzy + Gazebo Harmonic.
# Reference: https://github.com/Field-Robotics-Lab/dave (check the ROS 2 port branch).
# Pin a specific commit SHA so the build is reproducible:
#   ARG DAVE_REV=<sha>
#   RUN git clone --depth 1 https://github.com/Field-Robotics-Lab/dave.git /src/dave \
#       && cd /src/dave && git checkout ${DAVE_REV}
#   RUN cd /workspace && colcon build --packages-select <dave-packages>

# TODO(auv): install at least one stock DAVE AUV model (RexROV or LAUV).
# Mesh and config files should land under /workspace/poseidon-sim/auv_sim/
# at runtime via the bind mount in docker-compose.yml.

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
