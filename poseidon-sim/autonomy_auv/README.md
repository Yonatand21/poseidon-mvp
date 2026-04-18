# autonomy_auv (Layer 2)

Classical autonomy for the AUV. **Actuator-authoritative layer.** All
`/auv/thruster_cmd` and `/auv/fin_cmd` publishers live here.

**Design reference:** `SYSTEM_DESIGN.md` Section 8.8 (Nav-mode state
machine), Section 9.1 (AUV classical autonomy), Section 9.3 (Safety
invariants).

## Modules

| Dir | Purpose |
| --- | --- |
| `waypoint/` | Waypoint tracking, LOS path following, PID. |
| `depth_hold/` | Depth hold, altitude hold. |
| `bottom_follow/` | Bottom-following using DVL altitude and planned profile. |
| `survey/` | Lawnmower / area-coverage survey patterns. |
| `failsafe/` | Abort-to-surface, comms-timeout, critical-fault handlers. |
| `nav_state_machine/` | NOMINAL -> DEGRADED -> FALLBACK_INERTIAL -> ABORT_OR_LOITER. |
| `safety_invariants/` | Geofence, min-altitude, max-depth, max-speed, collision safeguards. |

## Safety rules

Per [AGENTS.md](../../AGENTS.md):

- Safety invariants evaluate unconditionally. Nothing in Layer 3 can weaken
  or delay them.
- `autonomy_auv/` may consume Layer 3 advisories on `/ai/*` topics but must
  have a classical fallback and MUST NOT block on AI availability.
- `autonomy_auv/` runs fully with `ai_mode: off`.
