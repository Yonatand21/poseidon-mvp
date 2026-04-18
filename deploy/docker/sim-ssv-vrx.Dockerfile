# poseidon-sim-ssv-vrx
#
# SSV runtime image: VRX on Gazebo Harmonic + ROS 2 Jazzy.
# Replaces the mock SSV runtime once integration is complete.
#
# Track: SSV runtime. Playbook: docs/runbooks/integration-ssv-vrx.md
# Contract: SYSTEM_DESIGN.md Section 14 (Interface contracts).
# Layer invariants: AGENTS.md Rule 1.1, 1.5.

ARG POSEIDON_IMAGE_REGISTRY=ghcr.io/yonatand21/poseidon-mvp
ARG POSEIDON_IMAGE_TAG=dev
FROM ${POSEIDON_IMAGE_REGISTRY}/poseidon-base-dev:${POSEIDON_IMAGE_TAG}

LABEL org.opencontainers.image.description="POSEIDON MVP - SSV runtime (VRX on Gazebo Harmonic)"
LABEL poseidon.runtime="vrx"
LABEL poseidon.vehicle="ssv"

ARG DEBIAN_FRONTEND=noninteractive

USER root

# TODO(ssv): install Gazebo Harmonic via the gazebosim apt repository.
# Reference: https://gazebosim.org/docs/harmonic/install_ubuntu
# Coordinate with the AUV runtime track: land Gazebo Harmonic in
# base-dev.Dockerfile so both runtimes share the layer. Keep this file lean.

# TODO(ssv): clone and colcon-build VRX for ROS 2 Jazzy + Gazebo Harmonic.
# Reference: https://github.com/osrf/vrx (main branch targets Harmonic+Jazzy).
# Pin a specific commit SHA so the build is reproducible:
#   ARG VRX_REV=<sha>
#   RUN git clone --depth 1 https://github.com/osrf/vrx.git /src/vrx \
#       && cd /src/vrx && git checkout ${VRX_REV}
#   RUN cd /workspace && colcon build --packages-select <vrx-packages>

# TODO(ssv): install the WAM-V USV model from VRX.
# Mesh and config files should land under /workspace/poseidon-sim/ssv_sim/
# at runtime via the bind mount in docker-compose.yml.

USER poseidon
WORKDIR /workspace

# TODO(ssv): default to the VRX launch file once implemented.
# CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && \
#      ros2 launch poseidon_ssv_sim ssv_vrx.launch.py"]
CMD ["bash", "-lc", "echo 'sim-ssv-vrx placeholder - see docs/runbooks/integration-ssv-vrx.md' && sleep infinity"]
