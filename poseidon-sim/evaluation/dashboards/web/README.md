# web dashboard (Streamlit)

Lightweight run-review UI. Reads the most recent MCAP (or a directory
of MCAPs) and shows:

- Per-run metadata (scenario name, seed, duration, `ai_mode`, model hashes).
- Core KPIs: mission success, path RMS, nav-mode transition timeline,
  time-to-detect-GNSS-denial, time-to-detect-GNSS-spoofing, USBL fix
  availability, DVL bottom-lock percentage.
- Navigation cascade chart: SSV position uncertainty vs. AUV position
  error, over time, colored by GNSS mode.
- AI disagreement timeline for `ai_mode: shadow` runs.

**Design reference:** `SYSTEM_DESIGN.md` Section 13 (Evaluation and
metrics), Section 13.4 (Comparison and sweep reports). This is the
lightweight "single-page UI" mentioned in Section 18.2.2 Phase 4 as a
stretch goal.

## Scope

This is intentionally a **stretch goal** per the 24-hour sprint plan.
Foxglove Studio covers live MCAP review. This Streamlit dashboard adds
a shareable read-only link ("the stakeholder demo URL"), so
non-technical reviewers do not need Foxglove installed.

## Running (local)

```bash
cd poseidon-sim/evaluation/dashboards/web
uv run --with streamlit --with mcap --with plotly streamlit run app.py \
    -- --recordings ../../../../recordings
```

Opens <http://localhost:8501>.

## Running (containerized - Profile A only)

Later, as a `dashboard` compose service built FROM poseidon-base-dev
with `streamlit`, `mcap`, and `plotly` installed. Not part of the core
profile.

## Status

- [x] Placeholder `app.py` skeleton.
- [ ] Real MCAP metric extraction (depends on metrics pipeline in
      [`../../metrics/`](../../metrics/) landing).
- [ ] Navigation cascade chart.
- [ ] AI disagreement timeline.

## Offline-first

The dashboard reads local MCAP files only. No external API calls, no
model-hub pulls. Consistent with the Profile B offline posture even
though the dashboard itself is mission-enhancing (Profile A).

## Related

- [`../../metrics/`](../../metrics/) - classical metric extractors.
- `SYSTEM_DESIGN.md` Section 13.3 (AI-specific metrics).
- Foxglove layouts at [`..`](..) for richer live-replay view.
