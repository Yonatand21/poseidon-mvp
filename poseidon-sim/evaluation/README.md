# evaluation (Layer 4 - offline)

Every run produces animation / replay, telemetry logs, and a metrics report.
Offline AI mines the archive for patterns, clusters failures, recommends
scenarios, and generates performance summaries.

**Design reference:** `SYSTEM_DESIGN.md` Section 13 (Evaluation and metrics)
and Section 13.5 (Evaluation AI).

## Subdirs

| Dir | Purpose |
| --- | --- |
| `metrics/` | Classical metric extractors from MCAP (path RMS, nav-mode transitions, time-to-detect-denial, etc.). |
| `plots/` | Plot generators (matplotlib/plotly). |
| `dashboards/` | Foxglove layouts, optional web dashboard definitions. |
| `reports/` | PDF / HTML report templates and generators. |
| `ai/log_miner/` | Log mining, pattern discovery, time-series motif finding. |
| `ai/failure_clustering/` | UMAP/t-SNE clustering of failure runs. |
| `ai/scenario_recommender/` | Coverage gap analysis; adversarial scenario suggestion. |
| `ai/performance_summarizer/` | LLM-generated executive summaries over sweeps. |

## Rules

Per `SYSTEM_DESIGN.md` Section 13.5 and `AGENTS.md`:

- Operates exclusively on recorded MCAP files and metric databases.
- Does not run inline with simulations and cannot affect runtime behavior
  of any prior run.
- Outputs are reports, plots, and scenario suggestions - never auto-committed
  scenario files or CI regressions. Human review required.
- LLM-generated narratives cite the MCAP runs and specific metrics they
  reference.
- Clustering and recommendation models are versioned; version is logged in
  every report.

## Offline mode

Layer 4 LLM-based summarization runs offline in edge deployments; no LLM API
calls are allowed in the critical path (`SYSTEM_DESIGN.md` Section 17.6).
