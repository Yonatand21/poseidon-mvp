# UE5 archetype setup runbook

How to bring up the choke-point archetype level in the `PoseidonUE`
project, spawn the AUV and SSV actors, and verify they move in response
to `/auv/state` and `/ssv/state` over the rosbridge.

Target audience: Yonatan during the 24-hour sprint Days 9-12. Also the
team later when new archetypes are added.

## Prerequisites

- `PoseidonUE` project opens cleanly in UE5 5.4. (If not, see
  [`../../poseidon-sim/rendering/unreal/PoseidonUE/README.md`](../../poseidon-sim/rendering/unreal/PoseidonUE/README.md).)
- `poseidon-sim` compose service up, publishing `/auv/state` and
  `/ssv/state` (real Stonefish on amd64, mock on Mac arm64).
- `unreal-bridge` compose service up, listening on `ws://<host>:9090`.
- ADR-0001 understood.

## One-time setup per archetype

### 1. Generate and copy the heightmap

Until `world_generator/` lands, use a 4097x4097 16-bit greyscale PNG
representing bathymetry (darker = deeper). A placeholder is acceptable
for the sprint; the real one arrives with Robbie's Day 1-2 archetype
generator.

Place the file at:

```text
poseidon-sim/rendering/unreal/PoseidonUE/Content/Archetypes/ChokePoint/Heightmap.png
```

The file is Git-LFS tracked via `.gitattributes`.

### 2. Open UE5 and create a new level

1. `File -> New Level -> Open World`.
2. `File -> Save Current Level As...`
   `Content/Archetypes/ChokePoint/Archetype.umap`.

### 3. Import the heightmap as a landscape

1. `Modes -> Landscape`.
2. `New Landscape -> Import From File -> Heightmap.png`.
3. Scale: X=100, Y=100, Z=100. Adjust `Location Z` so deepest point is
   around -5000 (50m below origin).
4. `Create`.

### 4. Add the ocean surface

1. In Content Browser, `Water` plugin folder, drag `BP_WaterBodyOcean`
   into the level.
2. Resize to cover the whole terrain in X/Y. Set Z to 0.
3. Under `Details -> Water`, set wave source to `Default Ocean`.

### 5. Add AUV and SSV actors

1. In the Content Browser, search for `VehicleActor` (the C++ class we
   built).
2. Drag two into the level. Name them `AUV` and `SSV` in the Outliner.
3. On the AUV: set `TopicName = /auv/state`, leave `MessageType` as
   default. Assign a visible mesh (UE5 cube or basic shape) to
   `SceneRoot`.
4. On the SSV: set `TopicName = /ssv/state`, same.

### 6. Add the bridge subsystem

`UPoseidonBridge` is a `UGameInstanceSubsystem` and is instantiated
automatically. On `BeginPlay`, call `Bridge->Connect("ws://localhost:9090")`
from a Level Blueprint or a `GameMode` override.

Minimum viable Level Blueprint:

- `Event BeginPlay` -> `Get Game Instance` -> `Get Subsystem
  (PoseidonBridge)` -> `Connect (ws://localhost:9090)`.

### 7. Test

1. Ensure the compose stack is up (`core` profile + `viz` profile).
2. Press Play in UE5.
3. Confirm AUV and SSV actors move in a circular loop (mock trajectory
   on Mac ARM64) or along the real scenario (cloud box).

## Expected behavior

- At 50 Hz, AUV position updates smoothly. UE Tick applies a damped
  interpolation so visual motion stays smooth even if the bridge
  delivers at lower rate.
- Coordinate convention: ROS ENU (+X east, +Y north, +Z up) is rotated
  into UE5 left-handed (X east, Y south, Z up). The `AVehicleActor`
  handles this.
- Units: ROS meters scaled by 100 to UE5 centimeters. `WorldScale` on
  `AVehicleActor` can be changed for debugging.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Actors sit at origin, do not move | Bridge not connected | Check `Output Log` for `[PoseidonBridge] connection error`. Verify `unreal-bridge` container is up and port 9090 reachable. |
| Actors move but not smoothly | Bridge delivering <10 Hz | Check `ros2 topic hz /auv/state` inside the sim container. Expected 50 Hz. |
| Actors move in the wrong direction | ENU vs UE5 coordinate mismatch | The `AVehicleActor` flips Y and quaternion signs to convert. If a specific scenario needs different handling, override `WorldScale` and rotation in the actor's Blueprint subclass. |
| Wave motion too strong / weak | Water System defaults not tuned for scene scale | Scale the `WaterBodyOcean` waveform parameters or swap in a custom wave generator. |
| Heightmap looks pixelated | Source PNG was 8-bit, not 16-bit | Re-export from `world_generator` with 16-bit PNG flag. |

## Next steps after this runbook

- Camera presets (Days 11-12) -
  [`ue5-camera-presets.md`](ue5-camera-presets.md) (created alongside).
- MCAP replay mode (Days 13-14) -
  [`ue5-mcap-replay.md`](ue5-mcap-replay.md) (created alongside).
