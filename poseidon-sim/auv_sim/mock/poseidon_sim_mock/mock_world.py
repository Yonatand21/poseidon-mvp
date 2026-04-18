"""Mock world publisher.

Publishes looping trajectories on /auv/state and /ssv/state as
nav_msgs/Odometry, plus a simple wave-state scalar vector on
/env/wave_state. Seed-determined so downstream consumers see repeatable
input across runs.

This is a stand-in for Stonefish on hosts where Stonefish does not build
(today: linux/arm64). It has no physics fidelity. It is not used on the
cloud box or in CI - those paths use the real sim.

AGENTS.md constraints honored:
- Publishes /auv/state and /ssv/state on behalf of Layer 1. These are
  ground-truth topics; evaluation consumes them. No actuator topics.
- Deterministic for a given seed.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import Quaternion
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Float32MultiArray


STATE_RATE_HZ = 50.0
ENV_RATE_HZ = 5.0

QOS_BEST_EFFORT = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


@dataclass
class TrajectoryParams:
    """Parameters of the looping trajectory published by the mock."""

    radius_m: float
    speed_mps: float
    depth_m: float
    phase_rad: float


def yaw_to_quaternion(yaw_rad: float) -> Quaternion:
    half = 0.5 * yaw_rad
    q = Quaternion()
    q.w = math.cos(half)
    q.z = math.sin(half)
    return q


class MockWorldNode(Node):
    def __init__(self) -> None:
        super().__init__("poseidon_sim_mock")

        self.declare_parameter("seed", 42)
        self.declare_parameter("auv_radius_m", 80.0)
        self.declare_parameter("ssv_radius_m", 200.0)
        self.declare_parameter("auv_speed_mps", 1.5)
        self.declare_parameter("ssv_speed_mps", 3.0)
        self.declare_parameter("auv_depth_m", 25.0)

        seed = int(self.get_parameter("seed").value)
        self._auv = TrajectoryParams(
            radius_m=float(self.get_parameter("auv_radius_m").value),
            speed_mps=float(self.get_parameter("auv_speed_mps").value),
            depth_m=float(self.get_parameter("auv_depth_m").value),
            phase_rad=(seed % 360) * math.pi / 180.0,
        )
        self._ssv = TrajectoryParams(
            radius_m=float(self.get_parameter("ssv_radius_m").value),
            speed_mps=float(self.get_parameter("ssv_speed_mps").value),
            depth_m=0.0,
            phase_rad=(seed % 360) * math.pi / 180.0 + math.pi / 4.0,
        )

        self._auv_pub = self.create_publisher(Odometry, "/auv/state", QOS_BEST_EFFORT)
        self._ssv_pub = self.create_publisher(Odometry, "/ssv/state", QOS_BEST_EFFORT)
        self._wave_pub = self.create_publisher(
            Float32MultiArray, "/env/wave_state", QOS_BEST_EFFORT
        )

        self._start_ns = self.get_clock().now().nanoseconds
        self._state_timer = self.create_timer(1.0 / STATE_RATE_HZ, self._publish_state)
        self._env_timer = self.create_timer(1.0 / ENV_RATE_HZ, self._publish_env)

        self.get_logger().info(
            f"poseidon_sim_mock up  seed={seed}  auv={self._auv}  ssv={self._ssv}"
        )

    def _elapsed_seconds(self) -> float:
        return (self.get_clock().now().nanoseconds - self._start_ns) * 1e-9

    def _sample_odometry(self, params: TrajectoryParams, frame_id: str) -> Odometry:
        t = self._elapsed_seconds()
        omega = params.speed_mps / max(params.radius_m, 1e-3)
        theta = omega * t + params.phase_rad

        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.child_frame_id = frame_id

        msg.pose.pose.position.x = params.radius_m * math.cos(theta)
        msg.pose.pose.position.y = params.radius_m * math.sin(theta)
        msg.pose.pose.position.z = -params.depth_m

        msg.pose.pose.orientation = yaw_to_quaternion(theta + math.pi / 2.0)

        msg.twist.twist.linear.x = -params.speed_mps * math.sin(theta)
        msg.twist.twist.linear.y = params.speed_mps * math.cos(theta)
        msg.twist.twist.angular.z = omega
        return msg

    def _publish_state(self) -> None:
        self._auv_pub.publish(self._sample_odometry(self._auv, "auv/base_link"))
        self._ssv_pub.publish(self._sample_odometry(self._ssv, "ssv/base_link"))

    def _publish_env(self) -> None:
        msg = Float32MultiArray()
        msg.data = [1.0, 0.12, 5.5, 8.0]
        self._wave_pub.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MockWorldNode()
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
