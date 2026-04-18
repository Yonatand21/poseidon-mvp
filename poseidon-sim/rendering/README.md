# rendering

Visual layer for POSEIDON.

- Visual path: UNav-Sim primary / PoseidonUE fallback.

Rendering is consumer-only. It never owns actuator authority or safety logic.

## Subdirs

| Dir | Purpose |
| --- | --- |
| `unreal/` | Unreal projects and assets (UNav-Sim integration + PoseidonUE fallback). |
| `bridge/` | ROS 2 to Unreal read-only bridge and allowlist configuration. |

## Non-responsibilities

- No simulation truth ownership.
- No control-loop authority.
- No mission orchestration.

