#!/usr/bin/env python3
"""Minimal SSV runtime publisher for federated MVP bring-up."""

from __future__ import annotations

import math
import os

import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import Quaternion
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Bool


QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


def yaw_to_quaternion(yaw_rad: float) -> Quaternion:
    half = 0.5 * yaw_rad
    q = Quaternion()
    q.w = math.cos(half)
    q.z = math.sin(half)
    return q


class MockSsvRuntime(Node):
    def __init__(self) -> None:
        super().__init__("mock_ssv_runtime")
        self.declare_parameter("seed", 42)
        self.declare_parameter("radius_m", 200.0)
        self.declare_parameter("speed_mps", 3.0)
        self.declare_parameter("state_rate_hz", 50.0)
        self.declare_parameter("health_rate_hz", 2.0)

        seed = int(self.get_parameter("seed").value)
        self._radius = float(self.get_parameter("radius_m").value)
        self._speed = float(self.get_parameter("speed_mps").value)
        self._omega = self._speed / max(self._radius, 1e-3)
        self._phase = (seed % 360) * math.pi / 180.0 + math.pi / 4.0
        self._start_ns = self.get_clock().now().nanoseconds

        self._state_pub = self.create_publisher(Odometry, "/ssv/state", QOS)
        self._clock_pub = self.create_publisher(Time, "/sim/ssv/clock", QOS)
        self._health_pub = self.create_publisher(Bool, "/sim/ssv/health", QOS)

        state_hz = max(float(self.get_parameter("state_rate_hz").value), 1.0)
        health_hz = max(float(self.get_parameter("health_rate_hz").value), 1.0)
        self.create_timer(1.0 / state_hz, self._publish_state_and_clock)
        self.create_timer(1.0 / health_hz, self._publish_health)

    def _elapsed_seconds(self) -> float:
        return (self.get_clock().now().nanoseconds - self._start_ns) * 1e-9

    def _publish_state_and_clock(self) -> None:
        t = self._elapsed_seconds()
        theta = self._omega * t + self._phase
        now = self.get_clock().now().to_msg()

        msg = Odometry()
        msg.header.stamp = now
        msg.header.frame_id = "map"
        msg.child_frame_id = "ssv/base_link"
        msg.pose.pose.position.x = self._radius * math.cos(theta)
        msg.pose.pose.position.y = self._radius * math.sin(theta)
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation = yaw_to_quaternion(theta + math.pi / 2.0)
        msg.twist.twist.linear.x = -self._speed * math.sin(theta)
        msg.twist.twist.linear.y = self._speed * math.cos(theta)
        msg.twist.twist.angular.z = self._omega
        self._state_pub.publish(msg)

        clock_msg = Time()
        clock_msg.sec = now.sec
        clock_msg.nanosec = now.nanosec
        self._clock_pub.publish(clock_msg)

    def _publish_health(self) -> None:
        self._health_pub.publish(Bool(data=True))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MockSsvRuntime()
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
