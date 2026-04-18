# poseidon_sim_mock

Minimal ROS 2 mock publisher used when full DAVE/VRX runtime stack is unavailable.

Purpose:

- Keep downstream nav/autonomy/render/eval development unblocked on constrained hosts.
- Publish placeholder state/env topics with stable contracts.

This package is not a physics simulator and is not used for determinism validation.

## Topics

- `/auv/state`
- `/ssv/state`
- `/env/wave_state`
