# poseidon_sim_mock

Tiny ROS 2 Python package that publishes placeholder `/auv/state` and
`/ssv/state` odometry so the full ROS 2 graph boots on hosts where
Stonefish is not available.

**When this is used:** the `sim` service in
[`deploy/compose/docker-compose.yml`](../../../deploy/compose/docker-compose.yml)
switches to `poseidon_sim_mock` on `linux/arm64` (Apple Silicon). On
`linux/amd64` the real Stonefish + `stonefish_ros2` launch runs instead.

**What it is not:** it is not a physics simulator. It publishes simple
looping trajectories so downstream consumers (nav, autonomy, scenario
engine, rendering bridge) can be developed and validated against live
topics on a Mac.

## Topics published

| Topic | Type | Rate |
| --- | --- | --- |
| `/auv/state` | `nav_msgs/Odometry` | 50 Hz |
| `/ssv/state` | `nav_msgs/Odometry` | 50 Hz |
| `/env/wave_state` | `std_msgs/Float32MultiArray` | 5 Hz |

## Running

Inside the `sim` container on arm64:

```bash
ros2 run poseidon_sim_mock mock_world
```

Or directly with Python (no ROS 2):

```bash
cd poseidon-sim/auv_sim/mock
python -m poseidon_sim_mock.mock_world
```

## Scope

Minimum viable. Once the ARM64 Stonefish path is unblocked upstream, this
package becomes unnecessary and can be retired. Tracked as a follow-up in
the post-hackathon roadmap.
