"""ROS 2 launch file for the Unreal bridge.

Starts rosbridge_server with the read-only topic allowlist defined in
rosbridge_server_allowlist.yaml, enforcing AGENTS.md Rule 1.1 (UE cannot
see actuator topics).
"""

from __future__ import annotations

from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    here = Path(__file__).resolve().parent
    allowlist_default = str(here / "rosbridge_server_allowlist.yaml")

    allowlist_arg = DeclareLaunchArgument(
        "allowlist",
        default_value=allowlist_default,
        description="Path to the rosbridge allowlist YAML.",
    )

    port_arg = DeclareLaunchArgument(
        "port",
        default_value="9090",
        description="TCP port for the rosbridge WebSocket endpoint.",
    )

    rosbridge = Node(
        package="rosbridge_server",
        executable="rosbridge_websocket",
        name="unreal_rosbridge",
        output="screen",
        parameters=[
            LaunchConfiguration("allowlist"),
            {"port": LaunchConfiguration("port")},
        ],
    )

    return LaunchDescription([allowlist_arg, port_arg, rosbridge])
