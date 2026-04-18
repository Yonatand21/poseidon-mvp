# scenarios

User-facing scenario YAML library. Each file defines a run: environment,
vehicles, mission phases, AI mode, metrics.

**Design reference:** `SYSTEM_DESIGN.md` Section 12 (Scenario engine),
Section 12.1 (full example YAML).

## Contract

Same scenario YAML + same seed + same `ai_mode` => same run.

- Schema lives in `../poseidon-sim/scenario_engine/schemas/`.
- Validator: Pydantic, invoked by the scenario engine on load.
- File naming: `<archetype>_<condition>_<role>.yaml`, e.g.
  `choke_point_gnss_denied_transit.yaml`.

## Planned library

| File | Archetype | Headline | Status |
| --- | --- | --- | --- |
| `hero_choke_point_gnss_denied.yaml` | choke_point | 24-hour hackathon demo run. | Planned for 24-hour sprint per Section 18.2. |
| `open_water_nominal_survey.yaml` | open_water | Baseline no-denial regression. | Planned for Week 7. |
| `continental_shelf_dvl_transition.yaml` | continental_shelf | Stresses DVL bottom-lock transitions. | Planned for Week 7. |
| `littoral_surface_wave_coupling.yaml` | littoral | Stresses shallow-water nav. | Planned for Week 7. |
| `harbor_approach_station_keep.yaml` | harbor_approach | SSV station keeping near hazards. | Planned for Week 7. |
| `spoof_progression.yaml` | choke_point | nominal -> jammed -> spoofed -> denied progression for AI headline metric. | Planned for Week 8. |

## Versioning

Scenario files are semver'd in a header comment once the schema freezes.
Breaking schema changes require a bumped `schema_version` field and a
migration note in `docs/architecture/`.
