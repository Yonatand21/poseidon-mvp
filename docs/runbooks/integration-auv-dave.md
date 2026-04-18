# AUV runtime integration - DAVE on Gazebo Harmonic

Track: AUV runtime. Replaces the mock AUV publisher with a real DAVE-backed Gazebo Harmonic runtime while preserving the Section 14 contract.

## Scope

This track owns:

- `poseidon-sim/auv_sim/`
- `deploy/docker/sim-auv-dave.Dockerfile`
- `poseidon-sim/auv_sim/launch/auv_dave.launch.py`

This track does not touch:

- `poseidon-sim/coupling/` (federation bridge)
- `poseidon-sim/ssv_sim/` (SSV runtime track)
- `poseidon-sim/autonomy_*/` (Layer 2)
- Topic names - remap only, never rename

## Hard contract (must not break)

Publish:

- `/auv/state` - `nav_msgs/Odometry`, 50 Hz
- `/auv/sensors/*` - DAVE sensor outputs remapped under this namespace
- `/sim/auv/clock` - `builtin_interfaces/Time`, 50 Hz
- `/sim/auv/health` - `std_msgs/Bool`, 2 Hz

Subscribe (Layer 2 publishes these; do not publish):

- `/auv/thruster_cmd`
- `/auv/fin_cmd`

## Starting point

1. Keep `poseidon-sim/auv_sim/src/mock_auv_runtime.py` as the arm64/Mac fallback.
2. Scaffold already committed:
   - `deploy/docker/sim-auv-dave.Dockerfile` (skeleton with TODOs)
   - `poseidon-sim/auv_sim/launch/auv_dave.launch.py` (skeleton with TODOs)
3. Validate your work: `python3 tests/integration/test_runtime_contract.py --vehicle auv`.

## Day-by-day (3-day target)

### Day 1 - shared base

Land Gazebo Harmonic in `deploy/docker/base-dev.Dockerfile` as a single PR so both AUV and SSV tracks reuse the layer. Coordinate with the SSV runtime track.

- Add the gazebosim apt repo and Harmonic install
- Run `bash tools/verify-backbone-t1.sh` - must still pass
- Land base-image PR before starting runtime work

### Day 2 - DAVE build

- Flesh out `sim-auv-dave.Dockerfile`
- Pin DAVE upstream: <https://github.com/Field-Robotics-Lab/dave> on the ROS 2 Jazzy / Harmonic branch
- Build one stock DAVE AUV (RexROV or LAUV) in the image
- Smoke test: `docker run` the image, launch the DAVE example, confirm gazebo topics appear

### Day 3 - topic remap + contract test

- Flesh out `auv_dave.launch.py`
- Remap DAVE native topics -> `/auv/state`, `/auv/sensors/*`
- Add a small Python shim (or ROS param) to emit `/sim/auv/clock` and `/sim/auv/health`
- Update `deploy/compose/docker-compose.yml`: flip `sim-auv` service to build `sim-auv-dave.Dockerfile`
- Run: `bash tools/verify-backbone-t1.sh --keep` must pass
- Run: `python3 tests/integration/test_runtime_contract.py --vehicle auv` must exit 0

## Definition of done

- Compose `--profile core` brings up DAVE-backed AUV
- `/auv/state`, `/auv/sensors/*`, `/sim/auv/clock`, `/sim/auv/health` present
- Tier-1 verification exits 0
- MCAP recording captures real DAVE state + sensors
- Federation bridge still publishes synchronized `/scenario/clock`

## Host requirement

- Linux + NVIDIA GPU (Tier-3 cloud box). DAVE will not build on Mac arm64.
- Use `docs/runbooks/cloud-demo-box.md` and `docs/runbooks/cloud-demo-box.provision.sh`.

## Branch and PR

- Branch: `feat/auv-dave-integration`
- Split the base-image update into its own small PR first
- Keep runtime PR under ~500 lines where possible
- PR into `main` once Tier-1 passes on the cloud box

## Ocean forcing note

Both runtimes subscribe to `/env/current` and `/env/wave_state` from `env-service`. DAVE's built-in current plugin must be overridden (or bypassed) so both vehicles feel the same ocean. Coordinate with the SSV runtime track on the schema (open question #2 in `SYSTEM_DESIGN.md`).

## Help and escalation

- Contract: `SYSTEM_DESIGN.md` Section 14
- Architecture invariant: `AGENTS.md` Rule 1.1
- Mock reference: `poseidon-sim/auv_sim/src/mock_auv_runtime.py`
- If DAVE build stalls: run DAVE's stock launch outside Docker first, iterate remaps against the contract test, then dockerize once working
