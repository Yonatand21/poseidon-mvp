# SSV runtime integration - VRX on Gazebo Harmonic

Track: SSV runtime. Replaces the mock SSV publisher with a real VRX-backed Gazebo Harmonic runtime while preserving the Section 14 contract.

## Scope

This track owns:

- `poseidon-sim/ssv_sim/`
- `deploy/docker/sim-ssv-vrx.Dockerfile`
- `poseidon-sim/ssv_sim/launch/ssv_vrx.launch.py`

This track does not touch:

- `poseidon-sim/coupling/` (federation bridge)
- `poseidon-sim/auv_sim/` (AUV runtime track)
- `poseidon-sim/autonomy_*/` (Layer 2)
- Topic names - remap only, never rename

## Hard contract (must not break)

Publish:

- `/ssv/state` - `nav_msgs/Odometry`, 50 Hz
- `/ssv/sensors/*` - VRX sensor outputs remapped under this namespace
- `/sim/ssv/clock` - `builtin_interfaces/Time`, 50 Hz
- `/sim/ssv/health` - `std_msgs/Bool`, 2 Hz

Subscribe (Layer 2 publishes these; do not publish):

- `/ssv/thruster_cmd`
- `/ssv/rudder_cmd`

## Starting point

1. Keep `poseidon-sim/ssv_sim/src/mock_ssv_runtime.py` as the arm64/Mac fallback.
2. Scaffold already committed:
   - `deploy/docker/sim-ssv-vrx.Dockerfile` (skeleton with TODOs)
   - `poseidon-sim/ssv_sim/launch/ssv_vrx.launch.py` (skeleton with TODOs)
3. Validate your work: `python3 tests/integration/test_runtime_contract.py --vehicle ssv`.

## Day-by-day (3-day target)

### Day 1 - shared base

Coordinate with the AUV runtime track on a single base-image PR that adds Gazebo Harmonic to `deploy/docker/base-dev.Dockerfile`. Whichever track lands it first unblocks both runtimes.

- Gazebo Harmonic apt repo + install
- `bash tools/verify-backbone-t1.sh` must still pass
- Land base-image PR before starting runtime work

### Day 2 - VRX build

- Flesh out `sim-ssv-vrx.Dockerfile`
- Pin VRX upstream: <https://github.com/osrf/vrx> (main branch is Harmonic + Jazzy compatible)
- Build WAM-V USV in the image
- Smoke test: `docker run` the image, launch a VRX task world, confirm gazebo topics appear

### Day 3 - topic remap + contract test

- Flesh out `ssv_vrx.launch.py`
- Remap VRX native topics -> `/ssv/state`, `/ssv/sensors/*`
- Add a small Python shim (or ROS param) for `/sim/ssv/clock` and `/sim/ssv/health`
- Update `deploy/compose/docker-compose.yml`: flip `sim-ssv` service to build `sim-ssv-vrx.Dockerfile`
- Run: `bash tools/verify-backbone-t1.sh --keep` must pass
- Run: `python3 tests/integration/test_runtime_contract.py --vehicle ssv` must exit 0

## Definition of done

- Compose `--profile core` brings up VRX-backed SSV
- `/ssv/state`, `/ssv/sensors/*`, `/sim/ssv/clock`, `/sim/ssv/health` present
- Tier-1 verification exits 0
- MCAP recording captures real VRX state + sensors
- Federation bridge still publishes synchronized `/scenario/clock`

## Host requirement

- Linux + NVIDIA GPU (Tier-3 cloud box). VRX runs on arm64 but GPU rendering / task worlds target Linux.
- Use `docs/runbooks/cloud-demo-box.md` and `docs/runbooks/cloud-demo-box.provision.sh`.

## Branch and PR

- Branch: `feat/ssv-vrx-integration`
- Split the base-image update into its own small PR first (or review the AUV track's PR if they land it first)
- Keep runtime PR under ~500 lines
- PR into `main` once Tier-1 passes on the cloud box

## Ocean forcing note

VRX has a native wave plugin. Disable or bypass it so both vehicles subscribe to `/env/wave_state` and `/env/current` from `env-service` for a single ocean truth. Coordinate with the AUV runtime track on the parameter schema.

## Help and escalation

- Contract: `SYSTEM_DESIGN.md` Section 14
- Architecture invariant: `AGENTS.md` Rule 1.1
- Mock reference: `poseidon-sim/ssv_sim/src/mock_ssv_runtime.py`
- If VRX build stalls: run VRX's stock launch outside Docker first, iterate remaps against the contract test, then dockerize once working
