# auv_sim (Layer 1)

Stonefish integration for the AUV. Vehicle plugin glue, sensor mount wiring,
and thruster/fin actuator bridging from ROS 2 commands.

**Design reference:** `SYSTEM_DESIGN.md` Section 6 (Vehicle modeling),
Section 7 (Sensors), Section 16 (Interface contracts).

## Topics

- Subscribes: `/auv/thruster_cmd`, `/auv/fin_cmd` (Layer 2 only).
- Publishes: `/auv/state` (ground truth, evaluation-only), all
  `/auv/sensors/*` outputs via the plugins under `sensor_models/`.

## Subdirs

- `src/` - ROS 2 nodes: state publisher, actuator bridge, plugin loader.
- `plugins/` - Stonefish C++ plugins for any sensor or actuator Stonefish
  does not ship by default.
