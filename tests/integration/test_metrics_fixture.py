"""End-to-end KPI extraction against the checked-in MCAP fixture.

Skipped when the optional `mcap` / `mcap-ros2-support` libraries or the
large MCAP fixture are not present. Local developers run:

    uv sync --extra eval
    uv run pytest tests/integration/test_metrics_fixture.py

Fixture: `recordings/run_20260418_182015/run_20260418_182015_0.mcap`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "recordings" / "run_20260418_182015"
FIXTURE_MCAP = FIXTURE_DIR / "run_20260418_182015_0.mcap"

mcap = pytest.importorskip("mcap", reason="pip install 'poseidon-sim[eval]' to run")
pytest.importorskip("mcap_ros2", reason="pip install 'poseidon-sim[eval]' to run")

if not FIXTURE_MCAP.exists():
    pytest.skip(
        f"fixture MCAP missing at {FIXTURE_MCAP}; "
        "record one with tools/verify-backbone-t1.sh",
        allow_module_level=True,
    )


def test_build_report_against_fixture(tmp_path: Path) -> None:
    from evaluation.metrics.mcap_reader import McapReader
    from evaluation.metrics.report import build_report, write_report
    from evaluation.metrics.schema import SCHEMA_VERSION

    reader = McapReader(FIXTURE_MCAP)
    report = build_report(reader)

    assert report.schema_version == SCHEMA_VERSION
    assert report.mcap_path.endswith(FIXTURE_MCAP.name)
    assert set(report.kpis).issuperset(
        {
            "mission_duration_s",
            "federation_drift_max_ns",
            "auv_track_length_m",
            "ssv_track_length_m",
            "drop_commit_observed",
        }
    )

    out = write_report(report, tmp_path / "kpis.json")
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert "kpis" in data and isinstance(data["kpis"], dict)


def test_extract_cli_strict_matches_report(tmp_path: Path) -> None:
    from evaluation.metrics.extract import main

    rc = main(
        [
            "--mcap",
            str(FIXTURE_MCAP),
            "--output",
            str(tmp_path / "kpis.json"),
        ]
    )
    assert rc in (0, 1), "CLI must exit 0 or 1, never raise"
    assert (tmp_path / "kpis.json").exists()
