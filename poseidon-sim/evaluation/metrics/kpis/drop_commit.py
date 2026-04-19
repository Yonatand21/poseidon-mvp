"""Whether the federation drop/commit event fired during the run.

`/federation/drop_commit` is an optional-but-expected event topic for
choke-point scenarios. Absence is not a hard contract violation (the
topic is scenario-dependent), so this KPI intentionally does not list
it in `CONTRACT_TOPICS`; it reports False + reason when missing rather
than being flagged by `--strict`.
"""

from __future__ import annotations

from ..mcap_reader import McapReader
from ..registry import register_kpi
from ..schema import KpiValue

DROP_COMMIT = "/federation/drop_commit"


@register_kpi(
    name="drop_commit_observed",
    required_topics=[DROP_COMMIT],
    description="True if at least one /federation/drop_commit message was recorded.",
)
def compute(reader: McapReader) -> KpiValue:
    for _ in reader.iter_messages(DROP_COMMIT):
        return KpiValue(value=True, unit="bool")
    return KpiValue(value=False, unit="bool", reason=f"no {DROP_COMMIT} messages")
