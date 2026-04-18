# sensor_models (Layer 1)

Sensor model wrappers and normalizers for federated runtime outputs.

Runtime source may be DAVE or VRX plugins, but published topic contracts are stable.

## Sensor families

- IMU
- depth
- DVL
- sonar
- GNSS
- compass
- radar
- camera
- USBL
- acoustic modem

## Contract

- Timestamped ROS 2 messages.
- Explicit frame IDs.
- Validity/dropout flags where applicable.
- Environment-coupled degradation hooks (`gnss_env`, `acoustic_env`, `env_service`).
