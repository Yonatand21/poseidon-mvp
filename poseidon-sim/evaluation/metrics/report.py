"""Report assembly and JSON persistence.

`build_report` is the single place that walks the KPI registry. Adding
a new KPI never requires touching this file.
"""

from __future__ import annotations

import json
from pathlib import Path

from .mcap_reader import McapReader
from .registry import KPI_REGISTRY, load_builtin_kpis
from .schema import CONTRACT_TOPICS, SCHEMA_VERSION, KpiReport, KpiValue


def _compute_one(reader: McapReader, available: frozenset[str], kpi) -> KpiValue:
    missing = [t for t in kpi.required_topics if t not in available]
    if missing:
        return KpiValue(
            value=None,
            unit="",
            reason=f"required topic(s) not recorded: {', '.join(missing)}",
        )
    try:
        return kpi.compute(reader)
    except Exception as exc:  # noqa: BLE001 - KPI failure must not abort the run
        return KpiValue(value=None, unit="", reason=f"{type(exc).__name__}: {exc}")


def build_report(reader: McapReader) -> KpiReport:
    """Run every registered KPI against the given MCAP reader."""
    load_builtin_kpis()

    available = reader.topics()
    missing_contract = sorted(CONTRACT_TOPICS.difference(available))

    report = KpiReport(
        schema_version=SCHEMA_VERSION,
        mcap_path=str(reader.path),
        recorded_topics=sorted(available),
        missing_contract_topics=missing_contract,
    )
    for kpi in KPI_REGISTRY:
        report.kpis[kpi.name] = _compute_one(reader, available, kpi)
    return report


def write_report(report: KpiReport, output_path: Path | str) -> Path:
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=False) + "\n")
    return path


def default_output_path(mcap_path: Path | str) -> Path:
    """Sibling `kpis.json` next to the MCAP (file or directory)."""
    p = Path(mcap_path).resolve()
    base = p if p.is_dir() else p.parent
    return base / "kpis.json"
