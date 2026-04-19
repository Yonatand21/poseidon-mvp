"""Offline metric extraction from MCAP recordings.

Public entry points:

- `McapReader` - thin wrapper around the Foxglove mcap + mcap-ros2 libs.
- `KPI_REGISTRY` / `register_kpi` - extensible KPI plugin surface.
- `build_report`, `write_report` - turn an MCAP into a `kpis.json` artifact.
- `extract.main` - CLI entry point wired into `verify-backbone-t1.sh`
  and CI as the runtime-contract gate.

Design notes in `SYSTEM_DESIGN.md` Section 13 and the Tier-2 runbook at
`docs/runbooks/tier-2-evaluation.md`.
"""

from .registry import KPI_REGISTRY, Kpi, register_kpi
from .report import build_report, write_report
from .schema import (
    CONTRACT_TOPICS,
    SCHEMA_VERSION,
    ContractViolation,
    KpiReport,
    KpiValue,
)

__all__ = [
    "CONTRACT_TOPICS",
    "ContractViolation",
    "KPI_REGISTRY",
    "Kpi",
    "KpiReport",
    "KpiValue",
    "SCHEMA_VERSION",
    "build_report",
    "register_kpi",
    "write_report",
]
