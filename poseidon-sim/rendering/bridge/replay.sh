#!/usr/bin/env bash
# replay.sh - play a recorded MCAP back into the UE5 pipeline.
#
# Usage:
#   bash poseidon-sim/rendering/bridge/replay.sh <mcap_path> [rate] [extra ros2 bag play args]
#
# Example:
#   bash poseidon-sim/rendering/bridge/replay.sh recordings/run_20260418_120000 1.0
#
# Behavior:
#   1. Stops the live sim and mcap-recorder compose services.
#   2. Ensures unreal-bridge is up.
#   3. Runs `ros2 bag play` inside the poseidon-base-dev image against the
#      given MCAP.
#
# Reference: docs/runbooks/ue5-mcap-replay.md

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: bash $0 <mcap_path> [rate] [extra ros2 bag play args]" >&2
    exit 1
fi

MCAP_PATH="$1"
RATE="${2:-1.0}"
shift 2 2>/dev/null || shift
EXTRA_ARGS="$*"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -e "$MCAP_PATH" ]]; then
    # tolerate "recordings/XXX" on the host even if also mounted at /recordings
    if [[ -e "${REPO_ROOT}/${MCAP_PATH}" ]]; then
        MCAP_PATH="${REPO_ROOT}/${MCAP_PATH}"
    else
        echo "MCAP not found: $MCAP_PATH" >&2
        exit 1
    fi
fi

echo "[replay] stopping live sim services"
docker compose -f deploy/compose/docker-compose.yml stop sim mcap-recorder >/dev/null 2>&1 || true

echo "[replay] starting unreal-bridge if needed"
docker compose -f deploy/compose/docker-compose.yml --profile viz up -d unreal-bridge

echo "[replay] playing ${MCAP_PATH} at rate ${RATE} ${EXTRA_ARGS}"
docker compose -f deploy/compose/docker-compose.yml run --rm \
    -v "${REPO_ROOT}/recordings:/recordings:ro" \
    sim ros2 bag play "/recordings/$(basename "${MCAP_PATH}")" \
        --rate "${RATE}" \
        ${EXTRA_ARGS}
