#!/usr/bin/env python3
"""SSV state adapter: gz dynamic_pose -> /ssv/state Odometry.

Subscribes directly to the Gazebo world dynamic-pose stream via
gz.transport13 (NOT through ros_gz_bridge). Filters the Pose_V for the
entity matching `target_frame`, computes velocity by numerical
differentiation, and publishes nav_msgs/Odometry to /ssv/state.

Why gz.transport13 instead of ros_gz_bridge:
- PR #6 deferred the /wamv/pose topic-type bug; cloud-box testing
  confirmed /wamv/pose only carries sensor mount transforms (camera/
  lidar/IMU/GPS positions relative to their parent body link), NOT the
  WAM-V's world->base_link pose.
- PR #7 added a ros_gz_bridge for /world/sydney_regatta/dynamic_pose/info
  (gz.msgs.Pose_V -> tf2_msgs/TFMessage); cloud-box testing confirmed the
  bridge's TFMessage converter silently drops entity names. Both
  frame_id and child_frame_id come through empty, so the adapter could
  never match `target_frame`.
- gz.transport13 subscribes directly to the Gazebo topic and gives full
  access to pose.name, which IS populated on the gz side (verified via
  `gz topic -e -t /world/sydney_regatta/dynamic_pose/info`).

Threading note:
- gz.transport13 subscriptions run callbacks on gz's internal thread,
  not the rclpy executor thread. rclpy.Publisher.publish() is
  documented as thread-safe (internal mutex), so calling it from the
  gz callback is fine. A small lock guards the velocity-differentiation
  state for safety.
"""
from __future__ import annotations

import math
import sys
import threading

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

# Gazebo Harmonic Python bindings - shipped with gz-harmonic in
# poseidon-base-dev (added by PR #3). If you change ROS distros or
# Gazebo versions these import paths will need to track the new ABI.
from gz.transport13 import Node as GzNode  # type: ignore[import-not-found]
from gz.msgs10.pose_v_pb2 import Pose_V  # type: ignore[import-not-found]


QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


def quat_to_yaw(qx: float, qy: float, qz: float, qw: float) -> float:
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


class SsvStateAdapter(Node):
    def __init__(self) -> None:
        super().__init__("ssv_state_adapter")

        # Source: Gazebo world dynamic-pose stream. The world name is
        # baked into the topic path; tracks ssv_vrx.launch.py's `world`
        # launch argument. If you change the VRX world, update both.
        self.declare_parameter(
            "gz_topic", "/world/sydney_regatta/dynamic_pose/info"
        )
        self.declare_parameter("output_topic", "/ssv/state")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("child_frame_id", "ssv/base_link")
        # Name of the entity in the gz Pose_V whose pose becomes
        # /ssv/state. For VRX competition.launch.py default WAM-V spawn
        # this is exactly "wamv" (verified via gz topic -e).
        self.declare_parameter("target_frame", "wamv")

        self._gz_topic = str(self.get_parameter("gz_topic").value)
        self._output_topic = str(self.get_parameter("output_topic").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        self._child_frame_id = str(self.get_parameter("child_frame_id").value)
        self._target_frame = str(self.get_parameter("target_frame").value)

        self._state_pub = self.create_publisher(
            Odometry, self._output_topic, QOS
        )

        self._last_x: float | None = None
        self._last_y: float | None = None
        self._last_yaw: float | None = None
        self._last_t: float | None = None
        # Guards numerical-differentiation state across gz callback
        # thread and any future rclpy timer threads.
        self._diff_lock = threading.Lock()
        self._logged_first_match: bool = False
        self._logged_no_match: bool = False

        self._gz_node = GzNode()
        subscribed = self._gz_node.subscribe(
            Pose_V, self._gz_topic, self._on_pose_v
        )
        if not subscribed:
            self.get_logger().error(
                f"failed to subscribe to gz topic '{self._gz_topic}'"
            )
            raise RuntimeError(f"gz subscribe failed: {self._gz_topic}")

        self.get_logger().info(
            f"ssv_state_adapter started: gz_topic='{self._gz_topic}', "
            f"target_frame='{self._target_frame}', "
            f"publishing {self._output_topic} as nav_msgs/Odometry "
            f"(frame_id={self._frame_id}, child={self._child_frame_id})"
        )

    def _on_pose_v(self, pose_v: Pose_V) -> None:
        """gz.transport callback - runs on gz's internal thread."""
        target_pose = None
        for pose in pose_v.pose:
            if pose.name == self._target_frame:
                target_pose = pose
                break

        if target_pose is None:
            if not self._logged_no_match:
                names = [p.name for p in pose_v.pose[:8]]
                self.get_logger().warn(
                    f"target_frame '{self._target_frame}' not in incoming "
                    f"Pose_V. First entity names seen: {names}"
                )
                self._logged_no_match = True
            return

        if not self._logged_first_match:
            self.get_logger().info(
                f"first /ssv/state publish: target_frame='{self._target_frame}' "
                f"matched at translation=({target_pose.position.x:.2f}, "
                f"{target_pose.position.y:.2f}, "
                f"{target_pose.position.z:.2f})"
            )
            self._logged_first_match = True

        # Prefer the gz Pose's own stamp; fall back to ROS wall clock if
        # zero (some publishers don't fill it in).
        gz_stamp = target_pose.header.stamp
        if gz_stamp.sec == 0 and gz_stamp.nsec == 0:
            ros_now = self.get_clock().now().to_msg()
            sec, nanosec = ros_now.sec, ros_now.nanosec
        else:
            sec, nanosec = int(gz_stamp.sec), int(gz_stamp.nsec)
        t_seconds = float(sec) + float(nanosec) * 1e-9

        x = float(target_pose.position.x)
        y = float(target_pose.position.y)
        z = float(target_pose.position.z)
        qx = float(target_pose.orientation.x)
        qy = float(target_pose.orientation.y)
        qz = float(target_pose.orientation.z)
        qw = float(target_pose.orientation.w)
        yaw = quat_to_yaw(qx, qy, qz, qw)

        with self._diff_lock:
            vx = 0.0
            vy = 0.0
            wz = 0.0
            if self._last_t is not None and t_seconds > self._last_t:
                dt = t_seconds - self._last_t
                if self._last_x is not None:
                    vx = (x - self._last_x) / dt
                if self._last_y is not None:
                    vy = (y - self._last_y) / dt
                if self._last_yaw is not None:
                    wz = (yaw - self._last_yaw) / dt
            self._last_x = x
            self._last_y = y
            self._last_yaw = yaw
            self._last_t = t_seconds

        odom = Odometry()
        odom.header.stamp.sec = sec
        odom.header.stamp.nanosec = nanosec
        odom.header.frame_id = self._frame_id
        odom.child_frame_id = self._child_frame_id

        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = z
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw

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
    main(sys.argv[1:])
