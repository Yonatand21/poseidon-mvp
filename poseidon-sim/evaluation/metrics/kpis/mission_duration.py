"""Mission duration from the federation `/scenario/clock` stream.

Clock topic timestamps are authoritative - we use `log_time_ns` as the
wall measurement of when each tick was observed on the federated bus.
For ai_mode:off determinism runs this equals sim-time exactly; for
ai-enabled runs clock drift is captured separately by
`federation_drift`.
"""

from __future__ import annotations

from ..mcap_reader import McapReader
from ..registry import register_kpi
from ..schema import KpiValue

SCENARIO_CLOCK = "/scenario/clock"


@register_kpi(
    name="mission_duration_s",
    required_topics=[SCENARIO_CLOCK],
    description="Wall-clock span of the /scenario/clock stream, in seconds.",
)
def compute(reader: McapReader) -> KpiValue:
    first_ns: int | None = None
    last_ns: int | None = None
    for m in reader.iter_messages(SCENARIO_CLOCK):
        if first_ns is None:
            first_ns = m.log_time_ns
        last_ns = m.log_time_ns
    if first_ns is None or last_ns is None:
        return KpiValue(value=None, unit="s", reason=f"no {SCENARIO_CLOCK} messages")
    return KpiValue(value=(last_ns - first_ns) / 1e9, unit="s")
