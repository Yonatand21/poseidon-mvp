# UE5 MCAP replay runbook

Play a recorded run back into the UE5 view for post-event review. Same
camera presets, same bridge, different source: `ros2 bag play` instead
of a live sim.

**Design reference:** `SYSTEM_DESIGN.md` Section 14.1 (Unreal replays MCAP
files), Section 17.5 (Unreal consumes recorded MCAP in edge deployments),
`INFRASTRUCTURE_DESIGN.md` Section 5.3 (MCAP storage tiering).

## Why this matters

Per Section 17.5 the **edge runtime does not ship Unreal.** In partner
environments, MCAP replay on an analyst workstation is the only way UE
touches a run. This workflow validates that path.

It also gives us a disaster-recovery fallback on demo day: if live sim
breaks, switch to a pre-recorded canonical MCAP and keep the show
running. `SYSTEM_DESIGN.md` Section 18.2.4 risk table calls this out.

## Topics that replay cleanly

The `mcap-recorder` service records `ros2 bag record -a`, so every
topic is captured. On replay, only topics in the
[`rosbridge_server_allowlist.yaml`](../../poseidon-sim/rendering/bridge/rosbridge_server_allowlist.yaml)
reach UE. That is the same allowlist from ADR-0001 - no special replay
mode, no bridge changes, no chance of accidentally exposing actuator
topics.

Replayable topics (what UE sees):

| Topic | Type | Needed for |
| --- | --- | --- |
| `/auv/state` | `nav_msgs/Odometry` | AUV actor motion |
| `/ssv/state` | `nav_msgs/Odometry` | SSV actor motion |
| `/env/wave_state` | `std_msgs/Float32MultiArray` | Water System |
| `/env/wind` | `geometry_msgs/Vector3Stamped` | Particle FX |
| `/env/visibility` | `std_msgs/Float32` | Fog density |
| `/coupling/drop_cmd` | `std_msgs/Empty` | Drop cinematic trigger |
| `/scenario/clock` | `builtin_interfaces/Time` | HUD overlay |
| `/scenario/event` | `std_msgs/String` | Event markers |
| `/ai/anomaly/gnss_spoof_flag` | `std_msgs/Bool` | HUD alert |
| `/ai/anomaly/nav_integrity_score` | `std_msgs/Float32` | HUD score |

## Running a replay

Assumes the repo is cloned and `core` + `viz` profiles have been brought
up at least once. Replace `<MCAP_PATH>` with a real recording path.

```bash
# Host (Mac or Linux): stop the live sim, keep the bridge and UE
docker compose -f deploy/compose/docker-compose.yml stop sim mcap-recorder

# Host: start the bridge alone (it stays up across replays)
docker compose -f deploy/compose/docker-compose.yml --profile viz up -d unreal-bridge

# Shell into any poseidon-base-dev container to play the bag
docker compose -f deploy/compose/docker-compose.yml run --rm \
  -v $PWD/recordings:/recordings:ro \
  sim ros2 bag play /recordings/<MCAP_PATH> --rate 1.0 --loop
```

In UE5, press Play. Cameras and vehicle actors behave identically to the
live case.

Convenience wrapper:

```bash
# Host
bash poseidon-sim/rendering/bridge/replay.sh recordings/run_20260418_120000
```

(see [`replay.sh`](../../poseidon-sim/rendering/bridge/replay.sh))

## Replay controls

`ros2 bag play` supports:

- `--rate 0.5` half-speed for close analysis of drop event.
- `--rate 2.0` double-speed to skim a long transit.
- `--loop` restart when finished.
- `--start-offset <seconds>` skip to the interesting part.
- `--topics /auv/state /ssv/state` replay only specific topics.

Pause/resume is via space bar in the terminal where `ros2 bag play` is
running.

## Verifying replay fidelity

For a scenario recorded with `ai_mode: off`, bit-identical replay of
`/auv/state` and `/ssv/state` is expected. Verify with `evo`:

```bash
docker compose -f deploy/compose/docker-compose.yml run --rm sim bash -c "
  ros2 bag play /recordings/run.mcap --topics /auv/state &
  sleep 5 &&
  ros2 topic echo /auv/state --qos-reliability reliable --once
"
```

Replay of `ai_mode: on` runs produces the same trajectory if and only if
the AI modules ran deterministically (pinned weights, pinned seeds).
Non-deterministic AI runs are flagged by the scenario engine; replays of
those may diverge in AI advisory timing but the classical path stays
deterministic.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| UE vehicles do not move during replay | Bridge not connected, or sim/mcap-recorder containers still holding the ROS_DOMAIN_ID | Stop sim + mcap-recorder; restart unreal-bridge; retry. |
| Replay finishes immediately | MCAP file mismatch (empty or wrong format) | `ros2 bag info /recordings/<file>` to inspect. |
| `ros2 bag play` complains about MCAP plugin | Base image missing `rosbag2_storage_mcap` | Already installed in `poseidon-base-dev`. If it happens, rebuild the image. |
| Clock in HUD jumps backward | `--loop` restarted the bag | Expected. Use `--start-offset` instead of `--loop` for linear review. |

## Related

- [`ue5-archetype-setup.md`](ue5-archetype-setup.md)
- [`ue5-camera-presets.md`](ue5-camera-presets.md)
- ADR-0001 bridge rationale.
