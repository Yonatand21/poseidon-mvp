# ssv_sim (Layer 1)

VRX/Gazebo Harmonic integration for the SSV runtime.

Dual-runtime ownership: this module is the SSV simulation-truth owner.

Responsibilities:

- Launch and configure SSV world/plugins.
- Bridge SSV control commands from Layer 2 topics.
- Publish normalized SSV ground-truth and sensor topics.
- Expose runtime clock and health signals to federation bridge.

## Topics

- Subscribes: `/ssv/thruster_cmd`, `/ssv/rudder_cmd` (Layer 2 only).
- Publishes: `/ssv/state`, `/ssv/sensors/*`, `/sim/ssv/clock`, `/sim/ssv/health`.

## Subdirs

- `src/` - ROS 2 launch/adapters and runtime wrappers.

