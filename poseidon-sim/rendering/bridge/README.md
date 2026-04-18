# rendering/bridge

Read-only ROS 2 to Unreal bridge used by UNav-Sim primary / PoseidonUE fallback.

## Responsibilities

- Expose selected vehicle/environment/federation topics over websocket.
- Enforce topic allowlist so Unreal clients cannot publish control topics.
- Keep topic contracts stable across UNav-Sim and PoseidonUE clients.

## Canonical subscribed topics

- `/auv/state`
- `/ssv/state`
- `/env/wave_state`
- `/env/visibility`
- `/scenario/clock`
- `/coupling/drop_cmd`
- `/federation/sync_state`

Actuator topics are intentionally excluded.

