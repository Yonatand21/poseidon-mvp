# Archetypes (UE5 content)

UE5 import targets for procedurally generated archetype heightfields and
associated assets. Outputs from `poseidon-sim/world_generator/output/to_unreal/`
land here.

**Design reference:** `SYSTEM_DESIGN.md` Section 5 (Bathymetry archetypes),
Section 14 (Unreal visual layer).

## Per-archetype layout

```
Content/Archetypes/<archetype>/
  Heightmap.png            exported from world_generator (Git LFS)
  Bathymetry_M.uasset      UE5 landscape material
  Archetype.umap           level file: landscape + water body + lights
  Archetype_BP.uasset      Blueprint that spawns the map + vehicle actors
```

## Current targets

| Dir | Status | Notes |
| --- | --- | --- |
| `ChokePoint/` | Placeholder | Hero demo archetype. Import pipeline lands Day 9-10. |

## Import pipeline

1. `world_generator/` emits `Heightmap.png` (16-bit PNG) and
   `archetype.json` with bounds, scale, feature locations.
2. The UE5 editor commandlet `ImportArchetype` (TBD; implemented as a
   Python EditorUtilityWidget script for the 24-hour sprint) reads the
   JSON, imports the heightmap into a Landscape actor, applies the
   `Bathymetry_M` material, and spawns an `WaterBody_Ocean` at the
   configured scale.
3. Vehicle actors (`AVehicleActor`) are placed at initial poses from
   the scenario YAML.

Until the import pipeline lands, archetype setup is manual inside the
UE5 editor:

1. `File -> New Level -> Open World`
2. `Modes -> Landscape -> Import from File -> Heightmap.png`
3. Add `WaterBodyOcean` from the Water plugin, scale to match terrain.
4. Drag two `AVehicleActor` instances in; set `TopicName` to `/auv/state`
   and `/ssv/state` respectively.
5. Save as `Content/Archetypes/ChokePoint/Archetype.umap`.

This manual path is documented in `docs/runbooks/ue5-archetype-setup.md`
(created alongside the rendering track work).
