#!/usr/bin/env python3
from __future__ import annotations

import math
import os

import rclpy
from geometry_msgs.msg import Quaternion
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from tf2_msgs.msg import TFMessage

QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)

def quat_to_yaw(q: Quaternion) -> float:
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class SsvStateAdapter(Node):
    def __init__(self) -> None:
        super().__init__("ssv_state_adapter")
        self.declare_parameter("input_topic", "/wamv/pose")
        self.declare_parameter("output_topic", "/ssv/state")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("child_frame_id", "ssv/base_link")

        self._input_topic = str(self.get_parameter("input_topic").value)
        self._output_topic = str(self.get_parameter("output_topic").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        self._child_frame_id = str(self.get_parameter("child_frame_id").value)

        self._state_pub = self.create_publisher(Odometry, self._output_topic, QOS)
        self._sub = self.create_subscription(TFMessage, self._input_topic, self._on_tf, QOS)

        self._last_x: float | None = None
        self._last_y: float | None = None
        self._last_yaw: float | None = None
        self._last_t: float | None = None

    def _on_tf(self, msg: TFMessage) -> None:
        base_tf = None
        for tf in msg.transforms:
            if tf.child_frame_id.endswith("/base_link"):
                base_tf = tf
                break

        if base_tf is None:
            return

        stamp = base_tf.header.stamp
        t = float(stamp.sec) + float(stamp.nanosec) * 1e-9

        x = float(base_tf.transform.translation.x)
        y = float(base_tf.transform.translation.y)
        z = float(base_tf.transform.translation.z)

        q = Quaternion()
        q.x = float(base_tf.transform.rotation.x)
        q.y = float(base_tf.transform.rotation.y)
        q.z = float(base_tf.transform.rotation.z)
        q.w = float(base_tf.transform.rotation.w)

        yaw = quat_to_yaw(q)

        vx = 0.0
        vy = 0.0
        wz = 0.0

        if self._last_t is not None and t > self._last_t:
            dt = t - self._last_t
            vx = (x - self._last_x) / dt if self._last_x is not None else 0.0
            vy = (y - self._last_y) / dt if self._last_y is not None else 0.0
            wz = (yaw - self._last_yaw) / dt if self._last_yaw is not None else 0.0

        self._last_x = x
        self._last_y = y
        self._last_yaw = yaw
        self._last_t = t

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self._frame_id
        odom.child_frame_id = self._child_frame_id

        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = z
        odom.pose.pose.orientation = q

        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = wz

        self._state_pub.publish(odom)

def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SsvStateAdapter()
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
