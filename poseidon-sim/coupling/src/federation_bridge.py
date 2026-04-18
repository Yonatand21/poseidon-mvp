#!/usr/bin/env python3
"""Federation bridge MVP: sync clocks, health, and one event path."""

from __future__ import annotations

import json
import os

import rclpy
from builtin_interfaces.msg import Time
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Bool, Empty, String


QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


class FederationBridge(Node):
    def __init__(self) -> None:
        super().__init__("federation_bridge")

        self._auv_clock: Time | None = None
        self._ssv_clock: Time | None = None
        self._auv_healthy = False
        self._ssv_healthy = False
        self._drop_seq = 0

        self.create_subscription(Time, "/sim/auv/clock", self._on_auv_clock, QOS)
        self.create_subscription(Time, "/sim/ssv/clock", self._on_ssv_clock, QOS)
        self.create_subscription(Bool, "/sim/auv/health", self._on_auv_health, QOS)
        self.create_subscription(Bool, "/sim/ssv/health", self._on_ssv_health, QOS)
        self.create_subscription(Empty, "/coupling/drop_cmd", self._on_drop_cmd, QOS)

        self._scenario_clock_pub = self.create_publisher(Time, "/scenario/clock", QOS)
        self._health_pub = self.create_publisher(Bool, "/federation/runtime_health", QOS)
        self._sync_pub = self.create_publisher(String, "/federation/sync_state", QOS)
        self._drop_commit_pub = self.create_publisher(String, "/federation/drop_commit", QOS)

        self.create_timer(0.1, self._publish_sync_state)  # 10Hz

    def _on_auv_clock(self, msg: Time) -> None:
        self._auv_clock = msg

    def _on_ssv_clock(self, msg: Time) -> None:
        self._ssv_clock = msg

    def _on_auv_health(self, msg: Bool) -> None:
        self._auv_healthy = msg.data

    def _on_ssv_health(self, msg: Bool) -> None:
        self._ssv_healthy = msg.data

    def _on_drop_cmd(self, _: Empty) -> None:
        self._drop_seq += 1
        commit = {
            "event": "drop_commit",
            "seq": self._drop_seq,
            "clock_sec": int(self._scenario_time().sec),
            "clock_nanosec": int(self._scenario_time().nanosec),
        }
        msg = String()
        msg.data = json.dumps(commit, sort_keys=True)
        self._drop_commit_pub.publish(msg)

    def _scenario_time(self) -> Time:
        # Deterministic policy for MVP: scenario clock is min(auv, ssv).
        if self._auv_clock is None and self._ssv_clock is None:
            t = Time()
            t.sec = 0
            t.nanosec = 0
            return t
        if self._auv_clock is None:
            return self._ssv_clock  # type: ignore[return-value]
        if self._ssv_clock is None:
            return self._auv_clock

        auv_ns = self._auv_clock.sec * 1_000_000_000 + self._auv_clock.nanosec
        ssv_ns = self._ssv_clock.sec * 1_000_000_000 + self._ssv_clock.nanosec
        chosen = self._auv_clock if auv_ns <= ssv_ns else self._ssv_clock
        return chosen

    def _publish_sync_state(self) -> None:
        scenario_clock = self._scenario_time()
        self._scenario_clock_pub.publish(scenario_clock)

        healthy = Bool()
        healthy.data = self._auv_healthy and self._ssv_healthy
        self._health_pub.publish(healthy)

        auv_ns = (
            self._auv_clock.sec * 1_000_000_000 + self._auv_clock.nanosec
            if self._auv_clock
            else 0
        )
        ssv_ns = (
            self._ssv_clock.sec * 1_000_000_000 + self._ssv_clock.nanosec
            if self._ssv_clock
            else 0
        )
        drift_ns = abs(auv_ns - ssv_ns)

        payload = {
            "auv_clock_seen": self._auv_clock is not None,
            "ssv_clock_seen": self._ssv_clock is not None,
            "drift_ns": drift_ns,
            "runtime_health": healthy.data,
            "drop_seq": self._drop_seq,
        }
        sync_state = String()
        sync_state.data = json.dumps(payload, sort_keys=True)
        self._sync_pub.publish(sync_state)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FederationBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main([arg for arg in os.sys.argv[1:]])
