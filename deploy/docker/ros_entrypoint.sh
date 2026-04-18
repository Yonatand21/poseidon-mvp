#!/usr/bin/env bash
# ROS 2 entrypoint for poseidon-* images.
# Sources the ROS 2 environment and any local overlay, then execs the
# passed command. Keep this file minimal; anything that needs to run
# before the user's command should live here.

set -e

# Source the base ROS 2 distro. ROS_DISTRO is set by the image build.
if [[ -n "${ROS_DISTRO:-}" ]] && [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
    # shellcheck disable=SC1090
    source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi

# Source an optional workspace overlay if present. Downstream images that
# build a colcon workspace at /workspace/install/setup.bash are picked up
# here automatically.
if [[ -f "/workspace/install/setup.bash" ]]; then
    # shellcheck disable=SC1091
    source "/workspace/install/setup.bash"
fi

exec "$@"
