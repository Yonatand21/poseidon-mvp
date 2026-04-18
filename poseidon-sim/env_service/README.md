# env_service (Layer 1)

Ocean state service. Publishes the environmental boundary conditions consumed
by vehicle physics and sensor models.

**Design reference:** `SYSTEM_DESIGN.md` Section 5 (Parameterized mission
environment) and Section 8.6 (Acoustic environment).

## Topics published

- `/env/current`
- `/env/wave_state`
- `/env/wind`
- `/env/visibility`
- `/env/sound_speed_profile`
- `/env/ambient_noise_dB`
- `/env/bathymetry_query` (service)

## Inputs

- Scenario YAML `environment` block (archetype, sea state, wind, current,
  visibility, acoustic environment).
- Heightfield emitted by `world_generator/` for bathymetry queries.

## Subdirs

- `src/` - node implementation (Python for orchestration, C++ for any
  timing-critical publisher).
- `config/` - parameter files keyed by archetype and sea state.
