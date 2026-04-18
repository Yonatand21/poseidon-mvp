"""POSEIDON MVP run-review dashboard (stretch goal).

Lightweight Streamlit app that lists recorded MCAPs and surfaces the
core KPIs for each run. Intended as a shareable read-only view for
stakeholders who do not have Foxglove installed.

Scope (24-hour sprint): list recordings, show scenario metadata, and a
placeholder KPI section. Real metric extraction lands as the metrics
pipeline in `poseidon-sim/evaluation/metrics/` comes online.

Design reference: SYSTEM_DESIGN.md Section 13 (Evaluation and metrics),
Section 18.2.2 Phase 4 (stretch single-page UI).

Run:
    uv run --with streamlit --with mcap --with plotly streamlit run app.py \\
        -- --recordings ../../../../recordings
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

try:
    import streamlit as st
except ImportError as exc:
    raise SystemExit(
        "streamlit not installed. Run with: "
        "uv run --with streamlit --with mcap --with plotly streamlit run app.py"
    ) from exc


@dataclass
class RunSummary:
    path: Path
    size_bytes: int
    modified: datetime
    scenario: str = "unknown"
    seed: int = 0
    ai_mode: str = "unknown"
    duration_s: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recordings",
        default="recordings",
        help="Path to the recordings directory (relative to CWD or absolute).",
    )
    # streamlit passes its own flags; ignore unknown
    args, _ = parser.parse_known_args()
    return args


def list_runs(recordings_dir: Path) -> list[RunSummary]:
    """List MCAP recordings in the directory (both files and directories).

    rosbag2 with MCAP storage produces a directory per run containing
    `metadata.yaml` plus one or more `.mcap` chunks. Accept either.
    """
    runs: list[RunSummary] = []
    if not recordings_dir.exists():
        return runs

    for entry in sorted(recordings_dir.iterdir(), reverse=True):
        if entry.is_dir():
            mcaps = list(entry.glob("*.mcap"))
            if not mcaps:
                continue
            size = sum(m.stat().st_size for m in mcaps)
            modified = datetime.fromtimestamp(max(m.stat().st_mtime for m in mcaps))
            runs.append(RunSummary(path=entry, size_bytes=size, modified=modified))
        elif entry.suffix == ".mcap":
            st_info = entry.stat()
            runs.append(
                RunSummary(
                    path=entry,
                    size_bytes=st_info.st_size,
                    modified=datetime.fromtimestamp(st_info.st_mtime),
                )
            )
    return runs


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def render_run_list(runs: Iterable[RunSummary]) -> RunSummary | None:
    st.sidebar.header("Recordings")
    runs = list(runs)
    if not runs:
        st.sidebar.info("No MCAP recordings found. Bring up the core compose profile to record a run.")
        return None
    labels = [
        f"{r.path.name}  ({human_bytes(r.size_bytes)}, {r.modified:%Y-%m-%d %H:%M})"
        for r in runs
    ]
    selected = st.sidebar.selectbox("Select a run", labels, index=0)
    return runs[labels.index(selected)]


def render_run_detail(run: RunSummary) -> None:
    st.title("POSEIDON MVP run review")
    st.caption(
        "Offline replay + KPI summary. SYSTEM_DESIGN.md Section 13. "
        "Foxglove covers live MCAP review; this is the shareable "
        "read-only view for stakeholders."
    )

    cols = st.columns(4)
    cols[0].metric("Scenario", run.scenario)
    cols[1].metric("Seed", f"{run.seed}")
    cols[2].metric("AI mode", run.ai_mode)
    cols[3].metric("Duration", f"{run.duration_s:.0f} s")

    st.subheader("Core KPIs")
    st.info(
        "Metric extraction pipeline lands with `poseidon-sim/evaluation/metrics/`. "
        "This section will populate automatically once that ships. "
        "For now, open the MCAP in Foxglove for interactive review: "
        f"`{run.path}`"
    )

    st.subheader("Navigation cascade (placeholder)")
    st.info(
        "Chart: SSV position uncertainty vs AUV position error over time, "
        "colored by GNSS mode. SYSTEM_DESIGN.md Section 13.2. "
        "Implementation pending Robbie's metrics pipeline."
    )

    st.subheader("AI disagreement timeline (placeholder)")
    st.info(
        "For `ai_mode: shadow` runs: classical vs AI decisions per module, "
        "per time. SYSTEM_DESIGN.md Section 13.3."
    )

    with st.expander("Run metadata"):
        st.json(
            {
                "path": str(run.path),
                "size": human_bytes(run.size_bytes),
                "modified": run.modified.isoformat(),
                "scenario": run.scenario,
                "seed": run.seed,
                "ai_mode": run.ai_mode,
                "duration_s": run.duration_s,
            }
        )


def main() -> None:
    args = parse_args()
    recordings_dir = Path(args.recordings).resolve()

    st.set_page_config(
        page_title="POSEIDON MVP run review",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.caption(f"Recordings dir: `{recordings_dir}`")
    runs = list_runs(recordings_dir)
    selected = render_run_list(runs)
    if selected is None:
        st.title("POSEIDON MVP run review")
        st.info("No runs yet. Record one with the `core` compose profile.")
        return
    render_run_detail(selected)


if __name__ == "__main__":
    main()
