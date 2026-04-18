# evaluation/metrics

Offline KPI extraction from MCAP recordings. Produces a stable
`kpis.json` next to each run that the Streamlit dashboard consumes and
that CI uses as the runtime-contract gate for AUV/SSV PRs.

Design reference: `SYSTEM_DESIGN.md` Section 13, Section 14.
Runbook: `docs/runbooks/tier-2-evaluation.md`.
Cross-track log: `docs/integration-log.md`.

## Install

```bash
uv sync --extra eval
```

`mcap` and `mcap-ros2-support` are isolated to the `eval` extra so
mission-essential core stays pip-dep free (AGENTS.md Section 3).

## CLI

```bash
python3 -m evaluation.metrics.extract --mcap recordings/run_<ts>/
python3 -m evaluation.metrics.extract --mcap <path> --strict   # contract-check mode
```

Exit codes:

- `0` - report written, all contract topics present, all KPIs computed.
- `1` - `--strict` and the report has at least one contract-topic miss
  or KPI failure.
- `2` - MCAP path not found or no `.mcap` chunks inside the directory.

## Extending

Drop a new module into `kpis/`:

```python
from ..mcap_reader import McapReader
from ..registry import register_kpi
from ..schema import KpiValue

@register_kpi(name="my_kpi_unit", required_topics=["/some/topic"])
def compute(reader: McapReader) -> KpiValue:
    ...
    return KpiValue(value=..., unit="...")
```

Then list the module in `kpis/__init__.py`. The CLI, report assembler,
and dashboard pick it up with no further edits.

## Schema stability

The `kpis.json` shape is fixed by `schema.py`. Changing
`SCHEMA_VERSION` is a breaking change - it must be coordinated with the
Streamlit dashboard and with the AUV/SSV tracks (they consume this
report in their PR CI).
