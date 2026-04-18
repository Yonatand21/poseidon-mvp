#!/usr/bin/env bash
# verify-backbone-t1.sh
#
# Tier 1 verification for the federated POSEIDON MVP backbone.
#
# Runs on any host with Docker available (primary target: Mac M4, but
# also works on Linux). Builds poseidon-base-dev for the host arch,
# smoke-tests it, colcon-builds the mock sim package inside, brings
# the `core` compose profile up, and verifies /auv/state, /ssv/state,
# and /scenario/clock are publishing.
#
# Does NOT build poseidon-sim runtime images. Uses base-dev plus mounted
# source for federated mock runtime bring-up.
#
# Usage:
#   bash tools/verify-backbone-t1.sh            # full run, logs to .verify-t1.log
#   bash tools/verify-backbone-t1.sh --keep     # leave containers up at end
#   bash tools/verify-backbone-t1.sh --pull     # pull images from GHCR instead of building
#
# Exit code 0 = pass, non-zero = fail with the failing step in the log.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOG_FILE="${REPO_ROOT}/.verify-t1.log"
KEEP_UP="no"
USE_PULL="no"
for arg in "$@"; do
    case "$arg" in
        --keep) KEEP_UP="yes" ;;
        --pull) USE_PULL="yes" ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

: > "$LOG_FILE"

GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

log()   { printf "[%s] %s\n" "$(date -u +%H:%M:%SZ)" "$1" | tee -a "$LOG_FILE"; }
pass()  { printf "%s[PASS]%s %s\n" "$GREEN" "$RESET" "$1" | tee -a "$LOG_FILE"; }
fail()  { printf "%s[FAIL]%s %s\n" "$RED" "$RESET" "$1" | tee -a "$LOG_FILE"; exit 1; }
info()  { printf "%s[info]%s %s\n" "$BOLD" "$RESET" "$1" | tee -a "$LOG_FILE"; }

cleanup() {
    if [[ "$KEEP_UP" != "yes" ]]; then
        info "tearing down compose"
        docker compose -f deploy/compose/docker-compose.yml down >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# ---- step 0: preflight ----
info "log file: $LOG_FILE"
info "host: $(uname -sm)"

if ! command -v docker >/dev/null 2>&1; then
    fail "docker CLI missing"
fi
if ! docker info >/dev/null 2>&1; then
    fail "docker daemon not responding - start Docker Desktop"
fi
pass "docker daemon reachable"

HOST_ARCH="$(uname -m)"
case "$HOST_ARCH" in
    arm64|aarch64) DOCKER_PLATFORM="linux/arm64" ;;
    x86_64)        DOCKER_PLATFORM="linux/amd64" ;;
    *)             fail "unsupported host arch: $HOST_ARCH" ;;
esac
info "target platform: $DOCKER_PLATFORM"

# ---- step 1: build or pull poseidon-base-dev ----
BASE_TAG="poseidon-base-dev:verify-t1"

if [[ "$USE_PULL" == "yes" ]]; then
    info "pulling poseidon-base-dev from GHCR"
    docker pull --platform "$DOCKER_PLATFORM" \
        ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev >> "$LOG_FILE" 2>&1 || \
        fail "GHCR pull failed (did CI push an image yet?)"
    docker tag ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev "$BASE_TAG"
else
    info "building poseidon-base-dev for $DOCKER_PLATFORM (expect ~5-10 min on first run)"
    docker buildx build \
        --platform "$DOCKER_PLATFORM" \
        --load \
        -f deploy/docker/base-dev.Dockerfile \
        -t "$BASE_TAG" \
        . 2>&1 | tee -a "$LOG_FILE" | tail -5 || fail "base-dev build failed"
fi
pass "poseidon-base-dev image present as $BASE_TAG"

# ---- step 2: smoke-test the base image ----
info "smoke test: ros2 --help"
docker run --rm --platform "$DOCKER_PLATFORM" "$BASE_TAG" bash -c "ros2 --help | head -3" \
    >> "$LOG_FILE" 2>&1 || fail "ros2 --help failed inside base image"
pass "ros2 --help runs"

info "smoke test: python3 version"
docker run --rm --platform "$DOCKER_PLATFORM" "$BASE_TAG" python3 --version \
    >> "$LOG_FILE" 2>&1 || fail "python3 missing"
pass "python3 runs"

info "smoke test: uv version"
docker run --rm --platform "$DOCKER_PLATFORM" "$BASE_TAG" uv --version \
    >> "$LOG_FILE" 2>&1 || fail "uv missing"
pass "uv runs"

# ---- step 3: colcon-build the mock sim package inside the image ----
# Use /workspace/ws (/workspace is owned by the poseidon user per
# base-dev.Dockerfile). Avoid /tmp/ws because Docker auto-creates -w
# directories as root, which breaks for non-root containers.
info "colcon-building poseidon_sim_mock inside the image"
docker run --rm --platform "$DOCKER_PLATFORM" \
    -v "${REPO_ROOT}/poseidon-sim/auv_sim/mock:/src/poseidon_sim_mock:ro" \
    "$BASE_TAG" bash -lc "
        set -e
        mkdir -p /workspace/ws/src
        cp -r /src/poseidon_sim_mock /workspace/ws/src/
        cd /workspace/ws
        source /opt/ros/jazzy/setup.bash
        colcon build --symlink-install 2>&1 | tail -20
        source install/setup.bash
        ros2 pkg list | grep poseidon_sim_mock
        ros2 pkg executables poseidon_sim_mock
    " 2>&1 | tee -a "$LOG_FILE" | tail -10 || fail "mock sim colcon build failed"
pass "poseidon_sim_mock colcon-builds and exposes mock_world executable"

# ---- step 4: run the mock briefly and check it publishes /auv/state ----
info "starting mock sim for 5s and checking /auv/state publishes"
docker run --rm --platform "$DOCKER_PLATFORM" \
    -v "${REPO_ROOT}/poseidon-sim/auv_sim/mock:/src/poseidon_sim_mock:ro" \
    "$BASE_TAG" bash -lc "
        set -e
        mkdir -p /workspace/ws/src
        cp -r /src/poseidon_sim_mock /workspace/ws/src/
        cd /workspace/ws
        source /opt/ros/jazzy/setup.bash
        colcon build --symlink-install > /dev/null 2>&1
        source install/setup.bash
        ros2 run poseidon_sim_mock mock_world &
        NODE_PID=\$!
        sleep 3
        TIMEOUT_OK=0
        timeout 3 ros2 topic hz /auv/state 2>&1 | head -5 && TIMEOUT_OK=1 || true
        kill \$NODE_PID 2>/dev/null || true
        if [[ \$TIMEOUT_OK -eq 1 ]]; then echo OK; else echo TIMEOUT; exit 1; fi
    " 2>&1 | tee -a "$LOG_FILE" | tail -10 || fail "mock sim did not publish /auv/state"
pass "mock sim publishes /auv/state"

# ---- step 5: docker compose up with local images, verify federated topics ----
# T1 aliases the base-dev image under the names the compose file
# references so compose uses local images instead of trying GHCR.
# POSEIDON_PULL_POLICY=never stops compose from attempting a pull.
info "aliasing local base image to names compose references"
docker tag "$BASE_TAG" ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev

info "bringing up core compose profile with local images"
export POSEIDON_PULL_POLICY=never
COMPOSE="docker compose -f deploy/compose/docker-compose.yml"

$COMPOSE --profile core up -d --no-build >> "$LOG_FILE" 2>&1 || fail "compose up failed (see $LOG_FILE)"

info "waiting up to 30s for federated services to publish key topics"
PUBLISHING_AUV=0
PUBLISHING_SSV=0
PUBLISHING_SCENARIO_CLOCK=0
for i in 1 2 3 4 5 6; do
    sleep 5
    if $COMPOSE exec -T sim-auv bash -lc "
        source /opt/ros/jazzy/setup.bash 2>/dev/null
        timeout 2 ros2 topic list 2>/dev/null | grep -q '^/auv/state$'
    " >> "$LOG_FILE" 2>&1; then
        PUBLISHING_AUV=1
    fi
    if $COMPOSE exec -T sim-ssv bash -lc "
        source /opt/ros/jazzy/setup.bash 2>/dev/null
        timeout 2 ros2 topic list 2>/dev/null | grep -q '^/ssv/state$'
    " >> "$LOG_FILE" 2>&1; then
        PUBLISHING_SSV=1
    fi
    if $COMPOSE exec -T federation-bridge bash -lc "
        source /opt/ros/jazzy/setup.bash 2>/dev/null
        timeout 2 ros2 topic list 2>/dev/null | grep -q '^/scenario/clock$'
    " >> "$LOG_FILE" 2>&1; then
        PUBLISHING_SCENARIO_CLOCK=1
    fi
    if [[ "$PUBLISHING_AUV" -eq 1 && "$PUBLISHING_SSV" -eq 1 && "$PUBLISHING_SCENARIO_CLOCK" -eq 1 ]]; then
        info "federated topics active after ${i}x5s"
        break
    fi
    info "attempt $i: topic readiness auv=$PUBLISHING_AUV ssv=$PUBLISHING_SSV scenario_clock=$PUBLISHING_SCENARIO_CLOCK"
done

$COMPOSE ps >> "$LOG_FILE"
if [[ "$PUBLISHING_AUV" -ne 1 || "$PUBLISHING_SSV" -ne 1 || "$PUBLISHING_SCENARIO_CLOCK" -ne 1 ]]; then
    echo "--- sim-auv logs (tail) ---" >> "$LOG_FILE"
    $COMPOSE logs sim-auv >> "$LOG_FILE" 2>&1 || true
    echo "--- sim-ssv logs (tail) ---" >> "$LOG_FILE"
    $COMPOSE logs sim-ssv >> "$LOG_FILE" 2>&1 || true
    echo "--- federation-bridge logs (tail) ---" >> "$LOG_FILE"
    $COMPOSE logs federation-bridge >> "$LOG_FILE" 2>&1 || true
    fail "federated services did not publish required topics within 30s; see $LOG_FILE"
fi
pass "federated compose services publish /auv/state, /ssv/state, and /scenario/clock"

# ---- step 6: recordings contract-check (optional, host-side) ----
# If any MCAPs exist under recordings/ AND the `mcap` + `mcap_ros2`
# libs are importable on the host, validate the newest one against the
# Section 14 runtime contract. Skipped gracefully otherwise so Tier 1
# stays runnable on hosts that haven't installed the eval extras.
info "looking for recordings to contract-check"
LATEST_MCAP="$(ls -1t recordings/*/*.mcap 2>/dev/null | head -1 || true)"
if [[ -z "${LATEST_MCAP}" ]]; then
    info "no MCAP under recordings/ - skipping contract-check"
elif ! python3 -c "import mcap, mcap_ros2" >/dev/null 2>&1; then
    info "mcap libs not installed on host - skipping contract-check"
    info "  (run: uv sync --extra eval)"
else
    info "contract-checking ${LATEST_MCAP}"
    if PYTHONPATH="${REPO_ROOT}/poseidon-sim" \
        python3 -m evaluation.metrics.extract \
            --mcap "${LATEST_MCAP}" \
            --strict \
            --no-write >> "$LOG_FILE" 2>&1; then
        pass "recordings contract-check passed for ${LATEST_MCAP##*/}"
    else
        fail "recordings contract-check FAILED for ${LATEST_MCAP} (see $LOG_FILE)"
    fi
fi

printf "\n%s[DONE]%s Tier 1 verification passed.\n" "$GREEN" "$RESET"
printf "Full log: %s\n" "$LOG_FILE"
if [[ "$KEEP_UP" == "yes" ]]; then
    printf "Containers left running. Teardown with:\n  %s down\n" "$COMPOSE"
fi
