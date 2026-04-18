"""Vehicle track length from `/auv/state` or `/ssv/state`.

One pure helper, two registrations. Keeps the AUV and SSV KPIs
symmetrical and avoids per-vehicle conditionals in the extractor.
"""

from __future__ import annotations

import math

from ..mcap_reader import McapReader
from ..registry import register_kpi
from ..schema import KpiValue


def _track_length_m(reader: McapReader, topic: str) -> KpiValue:
    prev: tuple[float, float, float] | None = None
    total = 0.0
    count = 0
    for m in reader.iter_messages(topic):
        pos = m.msg.pose.pose.position
        point = (float(pos.x), float(pos.y), float(pos.z))
        if prev is not None:
            dx = point[0] - prev[0]
            dy = point[1] - prev[1]
            dz = point[2] - prev[2]
            total += math.sqrt(dx * dx + dy * dy + dz * dz)
        prev = point
        count += 1
    if count == 0:
        return KpiValue(value=None, unit="m", reason=f"no {topic} messages")
    return KpiValue(value=total, unit="m")


@register_kpi(
    name="auv_track_length_m",
    required_topics=["/auv/state"],
    description="Integrated euclidean path length of the AUV from /auv/state.",
)
def auv(reader: McapReader) -> KpiValue:
    return _track_length_m(reader, "/auv/state")


@register_kpi(
    name="ssv_track_length_m",
    required_topics=["/ssv/state"],
    description="Integrated euclidean path length of the SSV from /ssv/state.",
)
def ssv(reader: McapReader) -> KpiValue:
    return _track_length_m(reader, "/ssv/state")
