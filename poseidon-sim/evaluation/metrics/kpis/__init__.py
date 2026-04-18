"""Built-in KPI modules.

Importing this package registers every bundled KPI with `KPI_REGISTRY`
as a side effect. New KPIs land as one new module listed below.

Adding a KPI:

1. Create `poseidon-sim/evaluation/metrics/kpis/<name>.py`.
2. Decorate a `McapReader -> KpiValue` function with
   `@register_kpi(name=..., required_topics=[...])`.
3. Add the module name to the import list here.
4. Add a unit test under `tests/unit/`.

No central dispatch edits, no CLI edits.
"""

from . import (  # noqa: F401  (import for side effect: KPI registration)
    drop_commit,
    federation_drift,
    mission_duration,
    track_length,
)
