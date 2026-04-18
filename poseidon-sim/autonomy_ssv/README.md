# autonomy_ssv (Layer 2)

Classical autonomy for the SSV. **Actuator-authoritative layer** for the SSV
(`/ssv/thruster_cmd`, `/ssv/rudder_cmd`).

**Design reference:** `SYSTEM_DESIGN.md` Section 9.2 (SSV classical
autonomy), Section 9.3 (Safety invariants). MOOS-IvP may back this stack
via a ROS 2 bridge (`OPEN_SOURCE_STACK.md` Section 2.5).

## Modules

| Dir | Purpose |
| --- | --- |
| `waypoint/` | Transit waypoint tracking. |
| `station_keep/` | Station keeping. NMPC is Phase 2; MVP uses PID with wind/current compensation. |
| `loiter/` | Loiter patterns for overwatch during AUV mission. |
| `escort/` | Escort / overwatch behavior relative to AUV position uncertainty. |
| `nav_state_machine/` | GNSS -> degraded-GNSS + IMU -> dead reckoning -> radar feature match. |
| `safety_invariants/` | Geofence, max-speed, collision safeguards, return-to-launch, comms-timeout. |

## Safety rules

Same as `autonomy_auv/`: safety invariants are unconditional, AI advisories
are optional inputs with classical fallback.
