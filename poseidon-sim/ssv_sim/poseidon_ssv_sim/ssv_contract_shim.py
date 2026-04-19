#!/usr/bin/env python3
from __future__ import annotations

import os

import rclpy
from builtin_interfaces.msg import Time
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Bool

QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)

class SsvContractShim(Node):
    def __init__(self) -> None:
        super().__init__("ssv_contract_shim")
        self.declare_parameter("clock_rate_hz", 50.0)
        self.declare_parameter("health_rate_hz", 2.0)

        self._clock_pub = self.create_publisher(Time, "/sim/ssv/clock", QOS)
        self._health_pub = self.create_publisher(Bool, "/sim/ssv/health", QOS)

        clock_hz = max(float(self.get_parameter("clock_rate_hz").value), 1.0)
        health_hz = max(float(self.get_parameter("health_rate_hz").value), 1.0)

        self.create_timer(1.0 / clock_hz, self._publish_clock)
        self.create_timer(1.0 / health_hz, self._publish_health)

    def _publish_clock(self) -> None:
        now = self.get_clock().now().to_msg()
        msg = Time()
        msg.sec = now.sec
        msg.nanosec = now.nanosec
        self._clock_pub.publish(msg)

    def _publish_health(self) -> None:
        self._health_pub.publish(Bool(data=True))

def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SsvContractShim()
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
