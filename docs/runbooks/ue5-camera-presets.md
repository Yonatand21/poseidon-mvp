# UE5 camera presets runbook

Three camera views for the POSEIDON demo, switchable by hotkeys 1/2/3
per `SYSTEM_DESIGN.md` Section 18.1 (Yonatan deliverable).

Target audience: Yonatan during Days 11-12 of the backbone plan, and
future demo-day operators.

## Presets

| Key | Preset | What it shows |
| --- | --- | --- |
| `1` | **Chase** | Third-person camera 10 m behind the AUV, 3 m above, auto-yaws to stay behind. Default at level start. |
| `2` | **Top-down** | Orthographic overview, altitude 250 m above the midpoint of AUV and SSV. Best for seeing the drop event in context. |
| `3` | **Drop cinematic** | Triggered by `/coupling/drop_cmd` or hotkey 3. Dolly-in from 25 m offset to a close-in 4 m framing over ~6 seconds, then auto-returns to Chase. |

The hotkey mappings live in
[`DefaultInput.ini`](../../poseidon-sim/rendering/unreal/PoseidonUE/Config/DefaultInput.ini):

```ini
+ActionMappings=(ActionName="CameraChase",Key=One)
+ActionMappings=(ActionName="CameraTopDown",Key=Two)
+ActionMappings=(ActionName="CameraDropCinematic",Key=Three)
```

## One-time setup in the UE5 editor

After running the archetype-setup runbook (`ue5-archetype-setup.md`):

1. In the World Outliner, select the `AUV` actor. Add tag `PoseidonAUV`.
2. Select the `SSV` actor. Add tag `PoseidonSSV`.
3. Drag an `APoseidonCameraDirector` into the level from the `Place
   Actors` panel (search `Poseidon`).
4. Leave its defaults (`ChaseOffsetMeters`, `TopDownAltitudeMeters`,
   `DropCinematicDurationSeconds`, `WorldScale=100`) as-is for sprint.
5. Open the Level Blueprint. On `BeginPlay`, the director auto-finds
   the tagged actors, connects to the bridge, and binds 1/2/3. No
   extra wiring needed.

Save the level. Press Play.

## Testing each preset

| Preset | Verification |
| --- | --- |
| Chase | AUV should stay centered in view while it moves. Camera yaws to follow. |
| Top-down | View is orthographic (parallel lines stay parallel); AUV and SSV visible simultaneously. |
| Drop cinematic | Either press `3` directly or publish `/coupling/drop_cmd` from a terminal: `docker exec -it poseidon-mvp-sim-1 ros2 topic pub --once /coupling/drop_cmd std_msgs/Empty "{}"`. Camera dollies in on the AUV for 6 seconds then returns to Chase. |

## Tuning for the hero demo

Suggested tweaks the night before demo day:

- **ChaseOffsetMeters:** `(-10, 0, 3)` is sprint default. For a more
  dramatic hero-shot feel try `(-15, 3, 4)` so you see a little of the
  AUV flank.
- **TopDownAltitudeMeters:** `250` shows context. Drop to `120` when the
  AUV is close to the SSV at release; raise to `400` for full-channel
  transit context.
- **DropCinematicDurationSeconds:** `6` feels natural. Do not go under
  `4` or the dolly-in looks jumpy.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Hotkeys 1/2/3 do nothing | Level Blueprint did not spawn the director, or PlayerController has focus of another widget | Confirm director is in the Outliner. Close any open UMG widget. |
| Chase camera jitters | ChaseOffsetMeters too short OR bridge rate too low | Increase offset to 15 m or raise the bridge rate (see ADR-0001). |
| Drop cinematic fires on every scenario tick | Someone publishing `/coupling/drop_cmd` at high rate | Scenario engine should publish once; check for a stuck republisher. Or disable the subscription temporarily by setting `/coupling/drop_cmd` out of the rosbridge allowlist (you lose the automatic trigger; keep hotkey 3 for manual). |
| Top-down camera clips into terrain | Altitude too low for archetype | Raise `TopDownAltitudeMeters`; choke-point needs at least 250 m at default archetype scale. |

## Future improvements (post-sprint)

- Cinematic spline cameras for onboard / cockpit views.
- HUD overlay on all presets showing nav mode, GNSS mode, current KPIs.
- Record-camera-as-MP4 via UE5's `MovieRenderQueue` for post-demo highlight reels.
- Multi-camera picture-in-picture: main view + minimap top-down.

## Related

- [`ue5-archetype-setup.md`](ue5-archetype-setup.md) - level setup.
- [`ue5-mcap-replay.md`](ue5-mcap-replay.md) - replay-mode behavior of
  the same camera presets.
- ADR-0001 at
  [`../architecture/0001-unreal-ros2-bridge.md`](../architecture/0001-unreal-ros2-bridge.md)
  for how the drop-cmd subscription works.
