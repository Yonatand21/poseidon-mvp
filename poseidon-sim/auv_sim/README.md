# auv_sim (Layer 1)

DAVE/Gazebo Harmonic integration for the AUV runtime.

Dual-runtime ownership: this module is the AUV simulation-truth owner.

Responsibilities:

- Launch and configure AUV world/plugins.
- Bridge AUV control commands from Layer 2 topics.
- Publish normalized AUV ground-truth and sensor topics.
- Expose runtime clock and health signals to federation bridge.

## Topics

- Subscribes: `/auv/thruster_cmd`, `/auv/fin_cmd` (Layer 2 only).
- Publishes: `/auv/state`, `/auv/sensors/*`, `/sim/auv/clock`, `/sim/auv/health`.

## Subdirs

- `src/` - ROS 2 launch/adapters and runtime wrappers.
- `plugins/` - runtime-specific extensions where upstream plugins are insufficient.

