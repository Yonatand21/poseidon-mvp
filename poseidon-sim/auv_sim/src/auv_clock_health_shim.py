#!/usr/bin/env python3
"""AUV runtime shim that publishes federation clock and health topics.

Intended use:
- real DAVE runtime publishes /auv/state
- this shim watches /auv/state
- it republishes /sim/auv/clock at 50 Hz using the latest observed stamp
- it republishes /sim/auv/health at 2 Hz based on recent /auv/state activity

This preserves the canonical contract expected by the federation bridge.
"""

from __future__ import annotations

import os
import rclpy
from builtin_interfaces.msg import Time
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Bool


QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


class AuvClockHealthShim(Node):
    def __init__(self) -> None:
        super().__init__("auv_clock_health_shim")

        self.declare_parameter("state_timeout_sec", 1.0)
        self.declare_parameter("clock_rate_hz", 50.0)
        self.declare_parameter("health_rate_hz", 2.0)

        self._state_timeout_sec = float(
            self.get_parameter("state_timeout_sec").value
        )
        clock_rate_hz = max(float(self.get_parameter("clock_rate_hz").value), 1.0)
        health_rate_hz = max(float(self.get_parameter("health_rate_hz").value), 1.0)

        self._last_state_stamp_msg: Time | None = None
        self._last_state_rx_ns: int | None = None

        self._clock_pub = self.create_publisher(Time, "/sim/auv/clock", QOS)
        self._health_pub = self.create_publisher(Bool, "/sim/auv/health", QOS)

        self._state_sub = self.create_subscription(
            Odometry,
            "/auv/state",
            self._on_state,
            QOS,
        )

        self.create_timer(1.0 / clock_rate_hz, self._publish_clock)
        self.create_timer(1.0 / health_rate_hz, self._publish_health)

    def _on_state(self, msg: Odometry) -> None:
        self._last_state_stamp_msg = msg.header.stamp
        self._last_state_rx_ns = self.get_clock().now().nanoseconds

    def _state_is_fresh(self) -> bool:
        if self._last_state_rx_ns is None:
            return False

        age_sec = (self.get_clock().now().nanoseconds - self._last_state_rx_ns) * 1e-9
        return age_sec <= self._state_timeout_sec

    def _publish_clock(self) -> None:
        clock_msg = Time()

        if self._last_state_stamp_msg is not None:
            clock_msg.sec = self._last_state_stamp_msg.sec
            clock_msg.nanosec = self._last_state_stamp_msg.nanosec
        else:
            now = self.get_clock().now().to_msg()
            clock_msg.sec = now.sec
            clock_msg.nanosec = now.nanosec

        self._clock_pub.publish(clock_msg)

    def _publish_health(self) -> None:
        self._health_pub.publish(Bool(data=self._state_is_fresh()))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = AuvClockHealthShim()
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
