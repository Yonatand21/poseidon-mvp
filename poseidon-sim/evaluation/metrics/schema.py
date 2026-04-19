"""Schemas, constants, and typed results for KPI extraction.

The `kpis.json` file written next to an MCAP is the stable contract
between this track, the Streamlit dashboard, and the AUV/SSV runtime
PRs' CI gate. Treat every field here as a public interface.

Bumping `SCHEMA_VERSION` is a breaking change - coordinate with the
Streamlit dashboard and `docs/runbooks/tier-2-evaluation.md` before
incrementing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION: int = 1

# SYSTEM_DESIGN.md Section 14. Keep these in lockstep with
# `tests/integration/test_runtime_contract.py`; that script validates
# the live ROS graph, this one validates recorded MCAPs.
CONTRACT_TOPICS: frozenset[str] = frozenset(
    {
        "/auv/state",
        "/ssv/state",
        "/scenario/clock",
        "/sim/auv/clock",
        "/sim/ssv/clock",
        "/federation/sync_state",
        "/federation/runtime_health",
    }
)


@dataclass(frozen=True, slots=True)
class KpiValue:
    """A single KPI result.

    `value is None` is the agreed encoding for "could not compute"
    (missing topic, empty stream, decode error). `reason` is required
    in that case so downstream tooling can surface the cause without
    re-reading the MCAP.
    """

    value: float | int | bool | None
    unit: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "unit": self.unit, "reason": self.reason}


@dataclass(slots=True)
class KpiReport:
    schema_version: int
    mcap_path: str
    recorded_topics: list[str]
    missing_contract_topics: list[str]
    kpis: dict[str, KpiValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mcap_path": self.mcap_path,
            "recorded_topics": sorted(self.recorded_topics),
            "missing_contract_topics": sorted(self.missing_contract_topics),
            "kpis": {name: kv.to_dict() for name, kv in sorted(self.kpis.items())},
        }

    def has_violations(self) -> bool:
        """True if any contract topic is missing or any KPI failed."""
        if self.missing_contract_topics:
            return True
        return any(kv.value is None for kv in self.kpis.values())


class ContractViolation(Exception):
    """Raised by `--strict` callers when a report has violations."""
