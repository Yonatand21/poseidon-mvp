# sensor_models (Layer 1)

Pluggable sensor model library. Each sensor is a ROS 2 node (or Stonefish
plugin) implementing the common interface: timestamp, frame, validity,
noise, latency, ground-truth association.

**Design reference:** `SYSTEM_DESIGN.md` Section 7 (Sensor architecture).

## Sensor list (per `sensor_models/*`)

| Dir | Sensor | Primary vehicle | Notes |
| --- | --- | --- | --- |
| `imu/` | IMU | both | Grade-configurable: MEMS / tactical / nav. |
| `depth/` | Depth (pressure) | AUV | Absolute depth always. |
| `dvl/` | Doppler Velocity Log | AUV | Bottom-lock + water-lock modes. |
| `sonar/` | Imaging sonar | AUV | Post-MVP: side-scan, forward-looking. |
| `gnss/` | GNSS | both | Mode-configurable (nominal/denied/jammed/spoofed/etc.). |
| `compass/` | Compass / magnetometer / gyrocompass | both | Heading. |
| `radar/` | Radar | SSV | Surface tracking + optional coastline match. |
| `camera/` | Camera | both | Visual nav, AI perception input. |
| `usbl/` | USBL (transceiver on SSV, responder on AUV) | both | Primary AUV acoustic fix. |
| `acoustic_modem/` | Acoustic modem | both | Pipe for acoustic comms, separate from nav. |

## Fidelity tiers

- `ideal` - zero noise, for control bring-up.
- `noisy` - bias, jitter, latency, dropout.
- `environment_coupled` - occlusion, turbidity, sea clutter, wave effects,
  range dependence, lock loss.

## Common interface

All sensor nodes consume ground truth from Stonefish and publish in the
appropriate `sensor_msgs/*` type where possible. GNSS and USBL additionally
subscribe to environment nodes (`nav/gnss_env`, `nav/acoustic_env`) to
transform ground-truth position/range into degraded observations.
