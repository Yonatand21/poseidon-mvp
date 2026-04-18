"""Runtime topic contract test.

Asserts that a Layer 1 runtime - mock, DAVE, or VRX - honors the
canonical topic contract from SYSTEM_DESIGN.md Section 14.

Runs against a live compose stack: assumes
`docker compose -f deploy/compose/docker-compose.yml --profile core up`
is running. Both John and Robbie should run this against their own
runtime during integration.

Usage:
    python3 tests/integration/test_runtime_contract.py --vehicle auv
    python3 tests/integration/test_runtime_contract.py --vehicle ssv
    python3 tests/integration/test_runtime_contract.py --vehicle both

Exit code 0 = contract satisfied, non-zero = violation printed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


AUV_REQUIRED_TOPICS = (
    "/auv/state",
    "/sim/auv/clock",
    "/sim/auv/health",
)

SSV_REQUIRED_TOPICS = (
    "/ssv/state",
    "/sim/ssv/clock",
    "/sim/ssv/health",
)

FEDERATION_REQUIRED_TOPICS = (
    "/scenario/clock",
    "/federation/runtime_health",
    "/federation/sync_state",
)


def docker_compose_exec(service: str, shell_cmd: str) -> tuple[int, str, str]:
    """Run a shell command inside a compose service."""
    cmd = [
        "docker", "compose",
        "-f", "deploy/compose/docker-compose.yml",
        "exec", "-T", service,
        "bash", "-lc", shell_cmd,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def list_topics(probe_service: str) -> set[str]:
    """Return the set of topics visible on the DDS bus from inside probe_service."""
    rc, out, err = docker_compose_exec(
        probe_service,
        "source /opt/ros/jazzy/setup.bash && timeout 5 ros2 topic list",
    )
    if rc != 0:
        print(f"ros2 topic list failed rc={rc} stderr={err!r}", file=sys.stderr)
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def assert_subset(required: tuple[str, ...], observed: set[str], label: str) -> list[str]:
    missing = [t for t in required if t not in observed]
    if missing:
        print(f"[FAIL] {label} missing topics: {missing}", file=sys.stderr)
    else:
        print(f"[PASS] {label} topics present ({len(required)})")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vehicle", choices=("auv", "ssv", "both"), default="both")
    parser.add_argument("--wait-sec", type=int, default=10,
                        help="Grace period for topics to appear after compose up.")
    args = parser.parse_args()

    time.sleep(max(args.wait_sec, 0))

    failures: list[str] = []

    # Probe from sim-auv container for AUV topics and federation
    if args.vehicle in ("auv", "both"):
        observed = list_topics("sim-auv")
        failures += assert_subset(AUV_REQUIRED_TOPICS, observed, "auv runtime")
        failures += assert_subset(FEDERATION_REQUIRED_TOPICS, observed, "federation from auv side")

    if args.vehicle in ("ssv", "both"):
        observed = list_topics("sim-ssv")
        failures += assert_subset(SSV_REQUIRED_TOPICS, observed, "ssv runtime")
        failures += assert_subset(FEDERATION_REQUIRED_TOPICS, observed, "federation from ssv side")

    if failures:
        print(f"\ncontract violations: {failures}", file=sys.stderr)
        return 1

    print("\nruntime contract OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
