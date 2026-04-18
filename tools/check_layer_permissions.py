#!/usr/bin/env python3
"""Layer-permission lint.

Enforces architectural rules from AGENTS.md and ADR-0001:

1. AGENTS.md Rule 1.1 - actuator topics may only be published by
   poseidon-sim/autonomy_auv/** and poseidon-sim/autonomy_ssv/**.
   Implementation planned once real publisher code exists; see the
   module docstring for the full walk + ast parse plan.

2. ADR-0001 - the rosbridge allowlist at
   poseidon-sim/rendering/bridge/rosbridge_server_allowlist.yaml must
   NOT contain any actuator topic. UE must remain read-only.

This script exits 0 on pass and 1 on violation.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ACTUATOR_TOPICS = (
    "/auv/thruster_cmd",
    "/auv/fin_cmd",
    "/ssv/thruster_cmd",
    "/ssv/rudder_cmd",
)


def _strip_yaml_comments(text: str) -> str:
    """Remove YAML comment lines so we do not false-positive on docstrings
    that mention forbidden topics for explanatory purposes.
    """
    out_lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.lstrip()
        if stripped.startswith("#"):
            continue
        if "#" in raw and not (raw.count('"') % 2 == 1 or raw.count("'") % 2 == 1):
            code, _, _ = raw.partition("#")
            out_lines.append(code)
        else:
            out_lines.append(raw)
    return "\n".join(out_lines)


def check_rosbridge_allowlist() -> list[str]:
    """Return list of violation messages. Empty list means pass."""
    path = REPO_ROOT / "poseidon-sim/rendering/bridge/rosbridge_server_allowlist.yaml"
    if not path.exists():
        return []
    text = _strip_yaml_comments(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for topic in ACTUATOR_TOPICS:
        if topic in text:
            violations.append(
                f"{path}: actuator topic '{topic}' present in UE allowlist. "
                "This violates ADR-0001 and AGENTS.md Rule 1.1."
            )
    return violations


def check_actuator_publishers() -> list[str]:
    """Walk poseidon-sim/ sources for actuator topic publishers.

    Placeholder. The real implementation will:

    1. Glob poseidon-sim/**/*.{py,cpp,h,hpp} excluding autonomy_auv/
       and autonomy_ssv/.
    2. Parse each file for rclpy `create_publisher` and rclcpp
       `create_publisher` / `advertise` calls.
    3. Extract the topic name argument.
    4. If the topic name matches any ACTUATOR_TOPICS, report a
       violation with file and line.

    Returns: empty list until the real implementation lands.
    """
    return []


def main() -> int:
    violations: list[str] = []
    violations.extend(check_rosbridge_allowlist())
    violations.extend(check_actuator_publishers())

    if violations:
        print("layer-permission lint: FAIL", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("layer-permission lint: OK (allowlist clean, publisher walk pending)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
