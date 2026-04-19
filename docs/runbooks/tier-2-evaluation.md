# Tier-2 evaluation pipeline

Track: evaluation + dashboards. Independent of AUV/SSV runtime integration - runs fully in parallel.

## Goal

Close the evidence chain from MCAP recording to the Streamlit operator dashboard so every run produces a reviewable summary and per-seed KPIs.

## Scope

This track owns:

- `poseidon-sim/evaluation/dashboards/web/app.py`
- `poseidon-sim/evaluation/metrics/`
- Any new readers for MCAP parsing into Python analyses

This track does not touch:

- `poseidon-sim/auv_sim/`
- `poseidon-sim/ssv_sim/`
- `poseidon-sim/coupling/` (federation bridge)
- Any simulation runtime code

## Inputs already in place

Every `bash tools/verify-backbone-t1.sh` run writes:

- `recordings/run_<timestamp>/run_<timestamp>_0.mcap` - full topic history
- `recordings/run_metadata.json` - scenario id, seed, drop timing

These are the only inputs the dashboard needs. No DAVE/VRX dependency.

## Day-by-day (3-day target)

### Day 1 - MCAP ingestion (DONE on `feat/tier-2-evaluation`)

- `mcap` + `mcap-ros2-support` added to `[project.optional-dependencies.eval]`
- `poseidon-sim/evaluation/metrics/mcap_reader.py` yields decoded messages per topic
- Registry + schema + report assembly landed with unit tests
- CLI: `python3 -m evaluation.metrics.extract --mcap <path> [--strict]`
- Wired into `tools/verify-backbone-t1.sh` (optional step 6) and a new
  `evaluation-metrics` CI job

Install locally:

```bash
uv sync --extra eval
uv run pytest tests/unit/test_metrics_registry.py
```

### Day 2 - KPI extractors (DONE)

Current KPI set (extend by dropping a new module in `kpis/`):

- `mission_duration_s` - span of `/scenario/clock`
- `federation_drift_max_ns` - peak `drift_ns` on `/federation/sync_state`
- `auv_track_length_m` - integrated distance from `/auv/state`
- `ssv_track_length_m` - integrated distance from `/ssv/state`
- `drop_commit_observed` - bool from `/federation/drop_commit`

Per-run artifact lands at `recordings/<run>/kpis.json`. Schema is fixed
by `SCHEMA_VERSION` in `evaluation/metrics/schema.py`; bumping it is a
coordinated change tracked in `docs/integration-log.md`.

### Day 3 - Streamlit UI

- Extend `poseidon-sim/evaluation/dashboards/web/app.py` to:
  - List all runs under `recordings/`
  - Click a run -> show KPIs + a pose timeline plot
  - Download link for the MCAP

Run locally:

```bash
cd poseidon-sim/evaluation/dashboards/web
uv run --with streamlit --with plotly streamlit run app.py -- --recordings ../../../../recordings
```

## Contract-gate role

This track is also the MCAP-level contract gate for Tracks A (AUV
DAVE) and B (SSV VRX). Runtime PRs on those tracks must include the
output of:

```bash
python3 -m evaluation.metrics.extract --mcap <their recording> --strict
```

exiting 0 before merging. Co-owned with `docs/integration-log.md`.

## Definition of done

- Dashboard lists the `run_20260418_182015` MCAP and shows the 5 KPIs
- KPI extractor unit tests pass (`pytest tests/unit/test_metrics_registry.py`)
- Fixture integration test passes (`pytest tests/integration/test_metrics_fixture.py`)
- `--strict` exits 0 against the fixture MCAP
- `evaluation-metrics` CI job green on `feat/tier-2-evaluation`
- README updated with the `streamlit run` command
- T2 section in `docs/runbooks/backbone-verification.md` passes cleanly

## Host requirement

- Any workstation. No Docker, no GPU, no DAVE/VRX. Runs entirely on the host Python environment.

## Branch and PR

- Branch: `feat/tier-2-evaluation`
- PR after KPI extractor tests pass
- Parallel-safe with the AUV/SSV PRs - disjoint directories

## Useful pointers

- Existing skeleton: `poseidon-sim/evaluation/dashboards/web/app.py`
- Existing MCAP fixture: `recordings/run_20260418_182015/run_20260418_182015_0.mcap`
- Metadata example: `recordings/run_metadata.json`
