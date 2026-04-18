# scenario_engine

The scenario file is the single source of truth for each run.

For fixed scenario + seed + ai mode, the run should be reproducible.

## Responsibilities

1. Validate scenario YAML schema.
2. Invoke `world_generator` to produce environment artifacts.
3. Emit runtime configs for:
   - DAVE AUV runtime
   - VRX SSV runtime
   - federation/time-sync bridge
4. Launch ROS 2 graph for both runtimes, federation, nav/autonomy, recorder, evaluation.
5. Drive mission phases and fault injections.
6. Publish `/scenario/clock`.
7. Finalize MCAP metadata and trigger evaluation pipeline.

## Stack

- Hydra for config composition.
- Pydantic for schema validation.
- pytest/hypothesis for determinism tests.

## MVP entrypoint

- `src/run_scenario_mvp.py` publishes one seed-locked drop event and writes
  run metadata to `/recordings/run_metadata.json`.

