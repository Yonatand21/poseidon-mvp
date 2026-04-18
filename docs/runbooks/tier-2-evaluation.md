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

### Day 1 - MCAP ingestion

- Add `mcap` Python lib dependency (`uv add mcap rosbags` or similar)
- Implement `poseidon-sim/evaluation/metrics/mcap_reader.py` yielding messages for a given topic
- Unit test: iterate `/auv/state` from the checked-in MCAP fixture

### Day 2 - KPI extractors

Minimum KPI set (3-5 metrics):

- Mission duration (scenario end - scenario start from `/scenario/clock`)
- Federation drift max (`drift_ns` from `/federation/sync_state`)
- AUV track length (integrate distance from `/auv/state`)
- SSV track length (integrate distance from `/ssv/state`)
- Drop commit detected (bool from `/federation/drop_commit`)

Each returns a scalar. Persist per-run KPIs as JSON next to the MCAP.

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

## Definition of done

- Dashboard lists the `run_20260418_182015` MCAP and shows the 5 KPIs
- KPI extractor unit tests pass
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
