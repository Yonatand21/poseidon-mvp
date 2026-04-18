"""Max observed federation drift between DAVE and VRX runtimes.

The federation bridge publishes `/federation/sync_state` with a
`drift_ns` field. During early development the bridge ships that state
as a `std_msgs/String` carrying a JSON payload; once the dedicated IDL
lands it will be a structured field. This KPI accepts both shapes so
the Tier-2 pipeline never blocks on federation bridge migrations.

Relevant to AGENTS.md Rule 1.2 (dual runtime authority) and
SYSTEM_DESIGN.md Section 14 federation topics.
"""

from __future__ import annotations

import json

from ..mcap_reader import McapReader
from ..registry import register_kpi
from ..schema import KpiValue

SYNC_STATE = "/federation/sync_state"

# Ordered list of (accessor, description) pairs. Try structured fields
# first, fall back to JSON-in-String. Adding a new transport shape is a
# single line here - never a branching edit.
_DRIFT_EXTRACTORS: tuple = (
    lambda m: getattr(m, "drift_ns", None),
    lambda m: getattr(m, "max_drift_ns", None),
    lambda m: getattr(m, "drift", None),
    lambda m: _from_json(getattr(m, "data", None), "drift_ns"),
    lambda m: _from_json(getattr(m, "data", None), "max_drift_ns"),
)


def _from_json(raw: str | None, key: str) -> int | None:
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return None
    value = payload.get(key) if isinstance(payload, dict) else None
    return int(value) if value is not None else None


def _extract_drift_ns(msg) -> int | None:
    for extractor in _DRIFT_EXTRACTORS:
        value = extractor(msg)
        if value is not None:
            return int(value)
    return None


@register_kpi(
    name="federation_drift_max_ns",
    required_topics=[SYNC_STATE],
    description="Peak absolute drift_ns reported on /federation/sync_state.",
)
def compute(reader: McapReader) -> KpiValue:
    peak: int | None = None
    count = 0
    for m in reader.iter_messages(SYNC_STATE):
        drift = _extract_drift_ns(m.msg)
        if drift is None:
            continue
        count += 1
        abs_drift = abs(drift)
        if peak is None or abs_drift > peak:
            peak = abs_drift
    if count == 0 or peak is None:
        return KpiValue(value=None, unit="ns", reason=f"no drift samples on {SYNC_STATE}")
    return KpiValue(value=peak, unit="ns")
