#!/usr/bin/env bash
# sim-entrypoint.sh - routes the sim service to Stonefish or the mock.
#
# Runs inside the sim container (poseidon-sim image). On amd64 hosts it
# launches stonefish_ros2's demo scene. On arm64 hosts (Apple Silicon
# dev), Stonefish is not available, so it colcon-builds the mock
# package from the bind-mounted source and runs it instead.
#
# Bind mounts expected:
#   /workspace/poseidon-sim (the repo's poseidon-sim/ directory)
#
# Reference:
#   - deploy/compose/docker-compose.yml (sim service)
#   - poseidon-sim/auv_sim/mock/README.md
#   - SYSTEM_DESIGN.md Section 18.2.1 (24-hour sprint scope, mock path)

set -e

ARCH="$(uname -m)"

echo "[sim] host arch: $ARCH"

if [[ "$ARCH" == "x86_64" ]]; then
    echo "[sim] starting Stonefish + stonefish_ros2 demo"
    # shellcheck disable=SC1090,SC1091
    source "/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash"
    # stonefish_ros2 overlay was colcon-built at image-build time into
    # /workspace/install/. Source it if present; otherwise fall through.
    if [[ -f /workspace/install/setup.bash ]]; then
        # shellcheck disable=SC1091
        source /workspace/install/setup.bash
    fi
    exec ros2 launch stonefish_ros2 demo.launch.py
fi

# arm64 fallback - mock world publisher
echo "[sim] Stonefish not available on $ARCH; using poseidon_sim_mock"

MOCK_SRC="/workspace/poseidon-sim/auv_sim/mock"
WS="/workspace/ws"
if [[ ! -d "$MOCK_SRC" ]]; then
    echo "[sim] ERROR: mock source not bind-mounted at $MOCK_SRC" >&2
    echo "[sim] check docker-compose.yml volumes section" >&2
    exit 1
fi

mkdir -p "$WS/src"
# cp -rn so repeated starts don't clobber a running build; symlinking
# the source directly is nicer but colcon does not like symlinks under
# src/.
cp -rn "$MOCK_SRC" "$WS/src/poseidon_sim_mock" 2>/dev/null || true

cd "$WS"
# shellcheck disable=SC1090,SC1091
source "/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash"

if [[ ! -f "$WS/install/setup.bash" ]] || [[ "$WS/src/poseidon_sim_mock/setup.py" -nt "$WS/install/setup.bash" ]]; then
    echo "[sim] colcon-building mock package"
    colcon build --symlink-install
fi

# shellcheck disable=SC1091
source "$WS/install/setup.bash"

echo "[sim] starting mock_world"
exec ros2 run poseidon_sim_mock mock_world
