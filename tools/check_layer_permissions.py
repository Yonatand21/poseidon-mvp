#!/usr/bin/env python3
"""Layer-permission lint placeholder.

Reserved for the CI check described in SYSTEM_DESIGN.md Section 16 and
AGENTS.md Rule 1.1: only poseidon-sim/autonomy_auv/** and
poseidon-sim/autonomy_ssv/** may publish to the actuator topics
(/auv/thruster_cmd, /auv/fin_cmd, /ssv/thruster_cmd, /ssv/rudder_cmd).

Implementation plan (lands when the first Python ROS 2 node ships):

1. Walk poseidon-sim/ for .py and .cpp source files.
2. Parse publisher creation calls (create_publisher, rclcpp::create_publisher).
3. Extract topic names.
4. For any actuator topic, assert the owning module is under autonomy_auv/
   or autonomy_ssv/.
5. Return non-zero on violation with a clear diagnostic.

Until that lands, this script is a no-op that exits 0 so CI stays green.
"""

from __future__ import annotations

import sys


def main() -> int:
    # Placeholder. See module docstring for the planned implementation.
    print("check_layer_permissions: placeholder, no checks implemented yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
