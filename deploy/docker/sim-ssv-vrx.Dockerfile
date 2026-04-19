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

# Install VRX rosdeps + colcon build the upstream workspace.
# Quote handling: --skip-keys takes a single bare token here. The previous
# form embedded double quotes inside an outer bash -lc "..." string, which
# terminated the outer quote prematurely and broke the build.
RUN bash -lc "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd /opt/vrx_ws && \
    rosdep install --from-paths src --ignore-src -r -y --skip-keys=ament_cmake_pycodestyle && \
    colcon build --merge-install"

RUN mkdir -p /opt/vrx_ws/install/share/vrx_gazebo/models/wamv/tmp && \
    chown -R poseidon:poseidon /opt/vrx_ws/install/share/vrx_gazebo/models/wamv

RUN echo 'source /opt/vrx_ws/install/setup.bash' >> /home/poseidon/.bashrc
ENV VRX_WS=/opt/vrx_ws
ENV GZ_SIM_RESOURCE_PATH=/opt/vrx_ws/install/share:${GZ_SIM_RESOURCE_PATH}

# Build the POSEIDON SSV ament package at IMAGE-BUILD time, not at
# container start. AGENTS.md Section 3 (Profile B) forbids runtime
# build/install steps in mission images. Runtime cost was previously
# ~10-30 sec per `compose up`; this also makes the image deterministic
# (the running container always matches the built image SHA).
COPY --chown=poseidon:poseidon poseidon-sim/ssv_sim /opt/poseidon_ssv_ws/src/poseidon_ssv_sim
RUN bash -lc "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    source /opt/vrx_ws/install/setup.bash && \
    cd /opt/poseidon_ssv_ws && \
    colcon build --merge-install --packages-select poseidon_ssv_sim"
RUN echo 'source /opt/poseidon_ssv_ws/install/setup.bash' >> /home/poseidon/.bashrc
ENV POSEIDON_SSV_WS=/opt/poseidon_ssv_ws

USER poseidon
WORKDIR /workspace

# Default entrypoint: launch the VRX-backed SSV runtime. The /workspace
# bind mount in docker-compose.yml is now read-only (per the compose
# fix) since the package is baked into the image; the mount stays only
# for live code-edit dev workflows that override this CMD.
CMD ["bash", "-lc", "source /opt/ros/${ROS_DISTRO}/setup.bash && \
     source /opt/vrx_ws/install/setup.bash && \
     source /opt/poseidon_ssv_ws/install/setup.bash && \
     ros2 launch poseidon_ssv_sim ssv_vrx.launch.py seed:=${POSEIDON_SCENARIO_SEED:-42}"]
