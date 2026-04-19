"""Registry and schema tests. Do not require the mcap library."""

from __future__ import annotations

import pytest
from evaluation.metrics.registry import KPI_REGISTRY, Kpi, load_builtin_kpis
from evaluation.metrics.schema import (
    CONTRACT_TOPICS,
    SCHEMA_VERSION,
    KpiReport,
    KpiValue,
)


def _dummy_compute(_reader):  # pragma: no cover - registration-only double
    return KpiValue(value=0.0, unit="")


def test_builtin_kpis_register_without_error() -> None:
    load_builtin_kpis()
    expected = {
        "mission_duration_s",
        "federation_drift_max_ns",
        "auv_track_length_m",
        "ssv_track_length_m",
        "drop_commit_observed",
    }
    assert expected.issubset(set(KPI_REGISTRY.names()))


def test_builtin_kpis_reference_only_contract_or_scenario_topics() -> None:
    load_builtin_kpis()
    allowed = CONTRACT_TOPICS | {"/federation/drop_commit"}
    for kpi in KPI_REGISTRY:
        for topic in kpi.required_topics:
            assert topic in allowed, (
                f"KPI {kpi.name!r} depends on {topic!r} which is neither a "
                "Section 14 contract topic nor the drop_commit event. Either "
                "add it to CONTRACT_TOPICS or document it as scenario-local."
            )


def test_registry_rejects_duplicate_registration() -> None:
    load_builtin_kpis()
    name = next(iter(KPI_REGISTRY)).name
    with pytest.raises(RuntimeError):
        KPI_REGISTRY.add(
            Kpi(name=name, required_topics=("/x",), compute=_dummy_compute)
        )


def test_kpi_requires_at_least_one_topic() -> None:
    with pytest.raises(ValueError):
        Kpi(name="bad", required_topics=(), compute=_dummy_compute)


def test_kpi_requires_non_empty_name() -> None:
    with pytest.raises(ValueError):
        Kpi(name="", required_topics=("/x",), compute=_dummy_compute)


def test_kpi_value_serializes_null_as_none() -> None:
    kv = KpiValue(value=None, unit="s", reason="no data")
    assert kv.to_dict() == {"value": None, "unit": "s", "reason": "no data"}


def test_report_detects_violation_from_missing_topic() -> None:
    r = KpiReport(
        schema_version=SCHEMA_VERSION,
        mcap_path="/tmp/x.mcap",
        recorded_topics=["/auv/state"],
        missing_contract_topics=["/ssv/state"],
    )
    assert r.has_violations() is True


def test_report_detects_violation_from_null_kpi() -> None:
    r = KpiReport(
        schema_version=SCHEMA_VERSION,
        mcap_path="/tmp/x.mcap",
        recorded_topics=sorted(CONTRACT_TOPICS),
        missing_contract_topics=[],
        kpis={"x": KpiValue(value=None, unit="m", reason="empty")},
    )
    assert r.has_violations() is True


def test_report_is_clean_when_contract_satisfied() -> None:
    r = KpiReport(
        schema_version=SCHEMA_VERSION,
        mcap_path="/tmp/x.mcap",
        recorded_topics=sorted(CONTRACT_TOPICS),
        missing_contract_topics=[],
        kpis={"x": KpiValue(value=1.0, unit="m")},
    )
    assert r.has_violations() is False


def test_schema_version_is_int() -> None:
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION >= 1
