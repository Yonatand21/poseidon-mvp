"""KPI plugin registry.

New KPIs are added by dropping a module into
`poseidon-sim/evaluation/metrics/kpis/` that calls `@register_kpi(...)`
on a pure function `McapReader -> KpiValue`. The extractor, CLI, and
dashboard pick them up automatically - there is no central dispatch
table to edit.

The registry is deliberately process-global and frozen after import.
Two registrations with the same name are a programming error and raise
at import time.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mcap_reader import McapReader
    from .schema import KpiValue

KpiFn = Callable[["McapReader"], "KpiValue"]


@dataclass(frozen=True, slots=True)
class Kpi:
    name: str
    required_topics: tuple[str, ...]
    compute: KpiFn
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("KPI name must be non-empty")
        if not self.required_topics:
            raise ValueError(f"KPI {self.name!r} must declare at least one required topic")


@dataclass(slots=True)
class _Registry:
    _items: dict[str, Kpi] = field(default_factory=dict)

    def add(self, kpi: Kpi) -> None:
        if kpi.name in self._items:
            raise RuntimeError(f"KPI already registered: {kpi.name!r}")
        self._items[kpi.name] = kpi

    def __iter__(self):
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, name: object) -> bool:
        return name in self._items

    def __getitem__(self, name: str) -> Kpi:
        return self._items[name]

    def names(self) -> list[str]:
        return sorted(self._items)


KPI_REGISTRY: _Registry = _Registry()


def register_kpi(
    name: str,
    required_topics: Iterable[str],
    description: str = "",
) -> Callable[[KpiFn], KpiFn]:
    """Decorator that registers a function as a named KPI."""

    topics = tuple(required_topics)

    def decorator(fn: KpiFn) -> KpiFn:
        KPI_REGISTRY.add(
            Kpi(
                name=name,
                required_topics=topics,
                compute=fn,
                description=description or (fn.__doc__ or "").strip().splitlines()[0]
                if fn.__doc__
                else "",
            )
        )
        return fn

    return decorator


def load_builtin_kpis() -> None:
    """Import the bundled KPI modules to trigger their @register_kpi calls.

    Idempotent. Safe to call multiple times.
    """
    from . import kpis  # noqa: F401  (import for side effect)
