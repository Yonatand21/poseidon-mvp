# rendering

Visual rendering is a consumer only. Unreal does not own physics.

**Design reference:** `SYSTEM_DESIGN.md` Section 14 (Unreal visual layer),
Section 16 (Bridge), `OPEN_SOURCE_STACK.md` Section 2.2 (Unreal, UNav-Sim,
Datasmith, Unreal Water System).

## Subdirs

| Dir | Purpose |
| --- | --- |
| `unreal/` | Unreal Engine 5 project sources. Blueprints, UNav-Sim assets, Water System scenes, camera presets, Datasmith imports for hero-asset vehicles. |
| `bridge/` | ROS 2 <-> Unreal bridge. Streams `/tf`, vehicle state, environment state into Unreal Blueprints at up to 60 Hz. Consumes MCAP for post-run replay. |

## Non-responsibilities

- No physics ownership.
- No sensor simulation authority (Unreal may render a camera feed for demo,
  but the sensor plugin in Stonefish is the authoritative sensor output).
- No scenario orchestration.
- No AI inference.

## Profile posture

- Profile A (Dev / Demo): Unreal enabled.
- Profile B (Edge / Mission): Unreal disabled. The `bridge/` tools remain
  available for analyst replay from MCAP.
