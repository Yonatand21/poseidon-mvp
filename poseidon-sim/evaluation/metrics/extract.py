"""KPI extraction + contract-check CLI.

Two modes, same command:

- Extraction: reads an MCAP, writes `kpis.json` next to it.
- Contract check (`--strict`): non-zero exit if any Section 14 topic is
  missing or any KPI failed. Runs in `tools/verify-backbone-t1.sh` and
  in the CI `contract-check` job against AUV/SSV/coupling PRs.

Invocation:

    python3 -m evaluation.metrics.extract --mcap <path> [--strict]
    # or, without setting PYTHONPATH:
    python3 poseidon-sim/evaluation/metrics/extract.py --mcap <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _ensure_importable() -> None:
    """Allow running this file directly without PYTHONPATH gymnastics."""
    here = Path(__file__).resolve()
    src_root = here.parents[2]  # .../poseidon-sim
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="evaluation.metrics.extract",
        description="Extract KPIs from a POSEIDON MCAP and optionally "
        "enforce the Section 14 runtime contract.",
    )
    parser.add_argument(
        "--mcap",
        required=True,
        help="Path to an .mcap file or a rosbag2 MCAP directory.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (defaults to kpis.json next to the MCAP).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any contract topic is missing or any KPI failed.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Compute and print the report but do not write JSON to disk.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _ensure_importable()
    from evaluation.metrics.mcap_reader import McapReader
    from evaluation.metrics.report import build_report, default_output_path, write_report

    args = _parse_args(argv)

    try:
        reader = McapReader(args.mcap)
    except FileNotFoundError as exc:
        print(f"[extract] {exc}", file=sys.stderr)
        return 2

    report = build_report(reader)

    if not args.no_write:
        output_path = Path(args.output) if args.output else default_output_path(args.mcap)
        write_report(report, output_path)
        print(f"[extract] wrote {output_path}")

    print(json.dumps(report.to_dict(), indent=2, sort_keys=False))

    if args.strict and report.has_violations():
        print("[extract] FAIL: contract violations detected", file=sys.stderr)
        for topic in report.missing_contract_topics:
            print(f"  missing contract topic: {topic}", file=sys.stderr)
        for name, kv in report.kpis.items():
            if kv.value is None:
                print(f"  kpi failed: {name} ({kv.reason})", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
