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
        # Default input topic now points at the Pose_V->TFMessage bridge
        # set up in ssv_vrx.launch.py. Each TFMessage carries every world
        # entity (buoys, terrain, WAM-V); we filter for `target_frame`.
        # Cloud-box validation showed VRX's /wamv/pose only carries
        # sensor mount transforms, not the WAM-V's world pose.
        self.declare_parameter("input_topic", "/ssv/world_pose_raw")
        self.declare_parameter("output_topic", "/ssv/state")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("child_frame_id", "ssv/base_link")
        # Name of the entity in the bridged Pose_V whose pose becomes
        # /ssv/state. For VRX competition.launch.py default WAM-V spawn
        # this is exactly "wamv" (verified via gz topic -e on
        # /world/sydney_regatta/dynamic_pose/info).
        self.declare_parameter("target_frame", "wamv")

        self._input_topic = str(self.get_parameter("input_topic").value)
        self._output_topic = str(self.get_parameter("output_topic").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        self._child_frame_id = str(self.get_parameter("child_frame_id").value)
        self._target_frame = str(self.get_parameter("target_frame").value)

        self._state_pub = self.create_publisher(Odometry, self._output_topic, QOS)
        self._sub = self.create_subscription(TFMessage, self._input_topic, self._on_tf, QOS)

        self._last_x: float | None = None
        self._last_y: float | None = None
        self._last_yaw: float | None = None
        self._last_t: float | None = None
        # One-shot logging so the first successful match is visible in
        # logs without spamming the steady-state output.
        self._logged_first_match: bool = False
        self._logged_no_match: bool = False

        self.get_logger().info(
            f"ssv_state_adapter started: subscribing {self._input_topic}, "
            f"target_frame='{self._target_frame}', "
            f"publishing {self._output_topic} as nav_msgs/Odometry "
            f"(frame_id={self._frame_id}, child={self._child_frame_id})"
        )

    def _on_tf(self, msg: TFMessage) -> None:
        base_tf = None
        for tf in msg.transforms:
            if tf.child_frame_id == self._target_frame:
                base_tf = tf
                break

        if base_tf is None:
            if not self._logged_no_match:
                # First time we receive a TFMessage that does not contain
                # our target frame. Log once with the available names so
                # the operator can adjust `target_frame` at runtime via
                # `ros2 param set`.
                names = [t.child_frame_id for t in msg.transforms[:8]]
                self.get_logger().warn(
                    f"target_frame '{self._target_frame}' not in incoming "
                    f"TFMessage. First child_frame_ids seen: {names}"
                )
                self._logged_no_match = True
            return

        if not self._logged_first_match:
            self.get_logger().info(
                f"first /ssv/state publish: target_frame='{self._target_frame}' "
                f"matched at translation=({base_tf.transform.translation.x:.2f}, "
                f"{base_tf.transform.translation.y:.2f}, "
                f"{base_tf.transform.translation.z:.2f})"
            )
            self._logged_first_match = True

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
