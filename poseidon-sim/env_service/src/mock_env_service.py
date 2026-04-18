#!/usr/bin/env python3
"""Minimal environment publisher for federated MVP bring-up."""

from __future__ import annotations

import os

import rclpy
from geometry_msgs.msg import Vector3Stamped
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Float32, Float32MultiArray


QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


class MockEnvService(Node):
    def __init__(self) -> None:
        super().__init__("mock_env_service")
        self._wave_pub = self.create_publisher(Float32MultiArray, "/env/wave_state", QOS)
        self._vis_pub = self.create_publisher(Float32, "/env/visibility", QOS)
        self._current_pub = self.create_publisher(Vector3Stamped, "/env/current", QOS)
        self.create_timer(0.2, self._publish)  # 5Hz

    def _publish(self) -> None:
        now = self.get_clock().now().to_msg()

        wave = Float32MultiArray()
        wave.data = [1.0, 0.12, 5.5, 8.0]
        self._wave_pub.publish(wave)

        visibility = Float32()
        visibility.data = 18.0
        self._vis_pub.publish(visibility)

        current = Vector3Stamped()
        current.header.stamp = now
        current.header.frame_id = "map"
        current.vector.x = 0.25
        current.vector.y = 0.1
        current.vector.z = 0.0
        self._current_pub.publish(current)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MockEnvService()
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
