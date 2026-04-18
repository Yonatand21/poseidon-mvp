# ssv_sim (Layer 1)

Stonefish integration for the SSV. Surface-vessel Fossen dynamics
coefficients, sensor mount wiring, and thruster/rudder actuator bridging.

**Design reference:** `SYSTEM_DESIGN.md` Section 6 (Vehicle modeling),
Section 7 (Sensors), `OPEN_SOURCE_STACK.md` Section 2.6 (Fossen MSS).

## Topics

- Subscribes: `/ssv/thruster_cmd`, `/ssv/rudder_cmd` (Layer 2 only).
- Publishes: `/ssv/state` (ground truth), all `/ssv/sensors/*`.

## Subdirs

- `src/` - ROS 2 nodes and Fossen coefficient configuration.
