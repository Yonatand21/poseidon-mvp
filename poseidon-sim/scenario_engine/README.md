# scenario_engine

The scenario file is the single artifact that defines a run. Same scenario +
same seed + same `ai_mode` => same run.

**Design reference:** `SYSTEM_DESIGN.md` Section 12 (Scenario engine).

## Responsibilities

1. Validate YAML against the schema in `schemas/`.
2. Invoke the archetype generator in `../world_generator/` to produce
   bathymetry, currents, traffic.
3. Emit the Stonefish scene XML referencing the vehicle configs under
   `../../vehicles/`.
4. Launch the ROS 2 graph: Stonefish, sensor nodes, nav nodes, classical
   autonomy, Layer 3 AI modules per the `ai` block, coupling, comms pipe,
   evaluation recorder.
5. Tick mission phases. Issue `/coupling/drop_cmd`, transition conditions,
   fault injections, GNSS schedule.
6. Manage the simulation clock; record MCAP for the configured duration.
7. On completion, invoke the evaluation pipeline in `../evaluation/`.

## Subdirs

- `src/` - orchestrator (Python), fault injector, mission-phase sequencer.
- `schemas/` - Pydantic / JSON Schema for scenario YAML. Hydra overlays.
- `scenarios/` - library scenarios owned by the engine (seed-locked
  regression runs). The user-facing scenario library lives in
  `../../scenarios/` at the repo root.

## Stack

- `Hydra` for config composition.
- `Pydantic` for schema validation.
- `pytest` + `hypothesis` for property-based determinism tests.

See `OPEN_SOURCE_STACK.md` Section 2.9.
