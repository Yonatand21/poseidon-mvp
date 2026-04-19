# poseidon-base-dev
#
# Profile A (Development / Demo) base image.
# INFRASTRUCTURE_DESIGN.md Section 3.1 (Image families),
# SYSTEM_DESIGN.md Section 17.4 (Platform compatibility matrix),
# OPEN_SOURCE_STACK.md Section 2.1 (ROS 2 Jazzy) and 2.9 (uv, Hydra, Pydantic).
#
# Target: Ubuntu 24.04 LTS + ROS 2 Jazzy.
# Multi-arch: linux/amd64 (cloud box, CI) and linux/arm64 (Apple Silicon dev).
#
# Consumers: every mission-essential application image (poseidon-sim,
# poseidon-nav, poseidon-autonomy, poseidon-scenario-engine, poseidon-eval)
# builds FROM this image.
#
# Build:
#   docker buildx build \
#     --platform linux/amd64,linux/arm64 \
#     -f deploy/docker/base-dev.Dockerfile \
#     -t ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev \
#     .

# hadolint ignore=DL3007
FROM ubuntu:24.04

LABEL org.opencontainers.image.source="https://github.com/Yonatand21/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP Profile A base - Ubuntu 24.04 + ROS 2 Jazzy"
LABEL org.opencontainers.image.licenses="TBD"
LABEL poseidon.profile="A"
LABEL poseidon.ros-distro="jazzy"

ARG TARGETARCH
ARG ROS_DISTRO=jazzy
ARG DEBIAN_FRONTEND=noninteractive

ENV ROS_DISTRO=${ROS_DISTRO} \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System baseline: locales, certs, gpg for signed repos, build essentials.
# hadolint ignore=DL3008,DL3015
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg2 \
        lsb-release \
        locales \
        software-properties-common \
        sudo \
        tzdata \
        git \
        git-lfs \
        vim-tiny \
        && locale-gen en_US.UTF-8 \
        && rm -rf /var/lib/apt/lists/*

# ROS 2 Jazzy apt repository (signed).
# Reference: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
# hadolint ignore=DL3008,DL3015
RUN add-apt-repository universe && \
    curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
        > /etc/apt/sources.list.d/ros2.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-ros-base \
        ros-${ROS_DISTRO}-rclpy \
        ros-${ROS_DISTRO}-rclcpp \
        ros-${ROS_DISTRO}-tf2 \
        ros-${ROS_DISTRO}-tf2-ros \
        ros-${ROS_DISTRO}-geometry-msgs \
        ros-${ROS_DISTRO}-nav-msgs \
        ros-${ROS_DISTRO}-sensor-msgs \
        ros-${ROS_DISTRO}-std-msgs \
        ros-${ROS_DISTRO}-rosbag2 \
        ros-${ROS_DISTRO}-rosbag2-storage-mcap \
        ros-${ROS_DISTRO}-robot-localization \
        ros-${ROS_DISTRO}-behaviortree-cpp \
        python3-colcon-common-extensions \
        python3-rosdep \
        && rm -rf /var/lib/apt/lists/*

# Gazebo Harmonic (LTS pair for ROS 2 Jazzy) + ros_gz bridge.
# Required by both AUV (DAVE) and SSV (VRX) runtime images; installed
# here so the shared Layer-1 simulation stack is one apt layer instead
# of being duplicated per-vehicle.
# Reference: https://gazebosim.org/docs/harmonic/install_ubuntu
# AGENTS.md Section 3: pinned apt repo, no runtime install.
# hadolint ignore=DL3008,DL3015
RUN curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
        -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(. /etc/os-release && echo ${UBUNTU_CODENAME}) main" \
        > /etc/apt/sources.list.d/gazebo-stable.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gz-harmonic \
        ros-${ROS_DISTRO}-ros-gz \
        && rm -rf /var/lib/apt/lists/*

# Build toolchain (needed for colcon builds of any downstream C++ package,
# including DAVE / VRX / ros_gz overlays in the poseidon-sim image).
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        pkg-config \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-pytest \
        && rm -rf /var/lib/apt/lists/*

# uv - pinned version for reproducibility. INFRASTRUCTURE_DESIGN.md Section
# 17.3 demands pinned wheelhouses at the edge; uv enforces that.
ARG UV_VERSION=0.4.30
RUN case "${TARGETARCH}" in \
        amd64)   UV_ARCH="x86_64-unknown-linux-gnu" ;; \
        arm64)   UV_ARCH="aarch64-unknown-linux-gnu" ;; \
        *) echo "unsupported TARGETARCH=${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl -fsSL "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${UV_ARCH}.tar.gz" \
        | tar -xz -C /usr/local/bin --strip-components=1 "uv-${UV_ARCH}/uv" "uv-${UV_ARCH}/uvx" && \
    uv --version

# Non-root user for volume-mount-friendly UIDs.
# 1000 is the default on Ubuntu desktops; 1001 is the ubuntu:24.04 default
# "ubuntu" user, which we remove to free UID 1000.
# hadolint ignore=DL3008
RUN userdel -r ubuntu 2>/dev/null || true && \
    groupadd -g 1000 poseidon && \
    useradd -m -u 1000 -g 1000 -s /bin/bash poseidon && \
    echo "poseidon ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/poseidon && \
    chmod 0440 /etc/sudoers.d/poseidon && \
    mkdir -p /workspace /recordings && \
    chown -R poseidon:poseidon /workspace /recordings

# Source ROS 2 for every shell opened in the container.
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/poseidon/.bashrc

USER poseidon
WORKDIR /workspace

# Entrypoint sources ROS 2 then execs the passed command. This means
# `docker run poseidon-base-dev ros2 topic list` works directly.
COPY deploy/docker/ros_entrypoint.sh /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
