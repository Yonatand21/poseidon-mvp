# nav

Navigation stacks and the environment-side GNSS/acoustic degradation nodes.

**Design reference:** `SYSTEM_DESIGN.md` Section 8 (Navigation architecture).

## Subdirs

| Dir | Layer | Purpose |
| --- | --- | --- |
| `auv_nav/` | 2 | EKF/UKF fusion: INS + DVL + USBL + TAN + surfaced GNSS. Uses `robot_localization`. |
| `ssv_nav/` | 2 | EKF/UKF fusion: GNSS + IMU + speed-log + optional feature-match. |
| `gnss_env/` | 1 | GNSS mode node. Transforms ground-truth position into reported position per mode (nominal/degraded/jammed/spoofed/denied/intermittent). |
| `acoustic_env/` | 1 | Acoustic-environment node. SSP, ambient noise, multipath severity. Feeds USBL and acoustic modem. |

## Outputs

- `/auv/state_estimate`, `/auv/nav_mode`, `/auv/position_uncertainty`
- `/ssv/state_estimate`, `/ssv/nav_mode`, `/ssv/position_uncertainty`

## Nav cascade

The platform's headline capability (Section 8.3): SSV GNSS degradation
propagates to the AUV via USBL. `gnss_env` drives SSV nav quality; SSV nav
quality sets USBL transmission quality; `auv_nav` inherits the degradation.
This cascade is implemented by composition of the per-vehicle nodes, not by
a dedicated "cascade" module.
