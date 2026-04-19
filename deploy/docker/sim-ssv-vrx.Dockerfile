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

# Gazebo Harmonic already comes from poseidon-base-dev.
# Keep this image focused on VRX build + runtime wiring.

ARG VRX_REF=v3.1.0

# VRX build dependencies.
# hadolint ignore=DL3008,DL3015
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-vcstool \
        python3-rosinstall-generator \
        python3-rosdep \
        python3-sdformat14 \
        ros-${ROS_DISTRO}-xacro \
        ros-${ROS_DISTRO}-ros-gz-interfaces \
        ros-${ROS_DISTRO}-topic-tools \
        && rm -rf /var/lib/apt/lists/*

# Clone and build VRX for ROS 2 Jazzy + Gazebo Harmonic.
RUN mkdir -p /opt/vrx_ws/src && \
    git clone https://github.com/osrf/vrx.git /opt/vrx_ws/src/vrx && \
    cd /opt/vrx_ws/src/vrx && \
    git checkout ${VRX_REF}

RUN rosdep init 2>/dev/null || true && \
    rosdep update

RUN bash -lc "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd /opt/vrx_ws && \
    rosdep install --from-paths src --ignore-src -r -y --skip-keys="ament_cmake_pycodestyle" && \
    colcon build --merge-install"

RUN mkdir -p /opt/vrx_ws/install/share/vrx_gazebo/models/wamv/tmp && \
    chown -R poseidon:poseidon /opt/vrx_ws/install/share/vrx_gazebo/models/wamv

RUN echo 'source /opt/vrx_ws/install/setup.bash' >> /home/poseidon/.bashrc
ENV VRX_WS=/opt/vrx_ws
ENV GZ_SIM_RESOURCE_PATH=/opt/vrx_ws/install/share:${GZ_SIM_RESOURCE_PATH}

USER poseidon
WORKDIR /workspace

# TODO(ssv): default to the VRX launch file once implemented.
# CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && \
#      ros2 launch poseidon_ssv_sim ssv_vrx.launch.py"]
CMD ["bash", "-lc", "echo 'sim-ssv-vrx placeholder - see docs/runbooks/integration-ssv-vrx.md' && sleep infinity"]
