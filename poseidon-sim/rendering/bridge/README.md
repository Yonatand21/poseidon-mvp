# rendering/bridge

ROS 2 <-> Unreal Engine bridge. Implements ADR-0001
([`docs/architecture/0001-unreal-ros2-bridge.md`](../../../docs/architecture/0001-unreal-ros2-bridge.md)).

**Design reference:** `SYSTEM_DESIGN.md` Sections 14 (Unreal visual layer)
and 16 (Bridge).

## Components

| File | Purpose |
| --- | --- |
| `rosbridge_server_allowlist.yaml` | Topic allowlist. Only read topics UE needs. **Actuator topics are NEVER in this list.** |
| `bridge.launch.py` | Launches `rosbridge_server` with the allowlist. |
| `Dockerfile` | Image build for the `unreal-bridge` compose service. |

## What UE subscribes to

Read-only WebSocket subscriptions. Per `AGENTS.md` Rule 1.1, actuator
topics (`/auv/thruster_cmd`, `/auv/fin_cmd`, `/ssv/thruster_cmd`,
`/ssv/rudder_cmd`) are absent from the allowlist and UE cannot see them.

| Topic | Type | Rate | Used for |
| --- | --- | --- | --- |
| `/auv/state` | `nav_msgs/Odometry` | 50 Hz | AUV actor transform |
| `/ssv/state` | `nav_msgs/Odometry` | 50 Hz | SSV actor transform |
| `/env/wave_state` | `std_msgs/Float32MultiArray` | 5 Hz | Water System params |
| `/env/wind` | `geometry_msgs/Vector3Stamped` | 5 Hz | Particle FX |
| `/env/visibility` | `std_msgs/Float32` | 1 Hz | Fog density |
| `/coupling/drop_cmd` | `std_msgs/Empty` | event | Drop-cinematic trigger |
| `/scenario/clock` | `builtin_interfaces/Time` | 10 Hz | Overlay HUD |
| `/ai/anomaly/gnss_spoof_flag` | `std_msgs/Bool` | event | HUD alert |

## Running locally

Via Compose (with the `viz` profile):

```bash
docker compose -f deploy/compose/docker-compose.yml --profile viz up unreal-bridge
```

The bridge listens on `ws://0.0.0.0:9090`. Inside the container the
port is 9090; the compose file maps it to host 9090.

## UE5 side

See [`../unreal/PoseidonUE/Source/PoseidonUE/Bridge/`](../unreal/PoseidonUE/Source/PoseidonUE/)
(created in Days 7-8). The `UPoseidonBridge` UObject owns the
`FWebSocketsModule` connection and dispatches incoming messages to
per-topic subscriber UObjects.

## Verifying the bridge without UE

```bash
# In any container with websocat or wscat
echo '{"op":"subscribe","topic":"/auv/state","type":"nav_msgs/Odometry"}' | \
    websocat --one-message ws://localhost:9090
```

Or use the browser-based demo at
<https://robotwebtools.github.io/roslibjs/examples/simple-browser.html>.
