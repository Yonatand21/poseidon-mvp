# world_generator (Layer 1)

Procedural, seeded, archetype-driven world generation. Produces heightfields,
obstacle sets, surface-traffic scripts, and current fields consistent with
scenario parameters.

**Design reference:** `SYSTEM_DESIGN.md` Section 5 (Bathymetry archetypes,
ocean forcing) and Section 12 (Scenario engine).

## Archetypes

Five first-class archetypes, each a Python module under `archetypes/`:

- `open_water` - deep, flat or gently sloping (500-3000 m).
- `continental_shelf` - sloping from 30 m to 400 m.
- `littoral` - coastal, 5-80 m, variable bottom texture.
- `choke_point` - narrow channel with shoaling flanks; the hero demo archetype.
- `harbor_approach` - shelving bottom, shipping channel, moored obstacles.

## Procedural primitives

- `procedural/heightfield/` - seeded heightfield generation (fractal noise,
  channel shaping, shoal placement).
- `procedural/obstacles/` - reefs, wrecks, pinnacles, buoys, moored vessels.
- `procedural/traffic/` - surface vessel tracks, lane patterns.
- `procedural/currents/` - uniform, tidal-reversing, along-channel, sheared.

## Outputs

- `output/to_stonefish/` - Stonefish heightfield + obstacle XML fragments.
- `output/to_unreal/` - glTF / heightmap PNG for UE5 rendering.

## Determinism

Same archetype + same params + same seed => bit-identical outputs. This is
enforced by the deterministic regression suite in `tests/determinism/`.
