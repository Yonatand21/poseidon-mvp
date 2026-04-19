"""VRX-backed SSV runtime launch.

Track: SSV runtime. Playbook: docs/runbooks/integration-ssv-vrx.md.
Contract: SYSTEM_DESIGN.md Section 14.

Current stage:
- launches stock VRX competition world headless
- bridges Gazebo dynamic-pose stream into /ssv/world_pose_raw
- adapter consumes that and publishes /ssv/state (nav_msgs/Odometry, 50 Hz)
- republishes /sim/ssv/clock and /sim/ssv/health via shim
- remaps first-pass VRX sensor topics into /ssv/sensors/*

World-pose source (from cloud-box validation):
- VRX's /wamv/pose only contains sensor mount transforms (camera/lidar
  positions relative to base_link), NOT the world->base_link pose.
- Gazebo publishes the WAM-V world pose on
  /world/sydney_regatta/dynamic_pose/info as gz.msgs.Pose_V at sim rate.
- We bridge that to ROS as a tf2_msgs/TFMessage on /ssv/world_pose_raw,
  then the adapter filters for the entry whose name matches
  `target_frame` (default "wamv") and converts it to Odometry.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    declare_seed = DeclareLaunchArgument(
        "seed",
        default_value="42",
        description=(
            "Deterministic seed for the VRX runtime. Propagated into the "
            "VRX competition launch include below so wave/wind/spawn "
            "randomization is reproducible. Required by AGENTS.md Section 2 "
            "(VRX runtime seed is a pinned MCAP determinism input)."
        ),
    )

    banner = LogInfo(msg=[
        "ssv_vrx.launch.py starting - seed=", LaunchConfiguration("seed"),
        " - VRX launch + contract shim + state adapter enabled.",
    ])

    # AGENTS.md Section 2: pass scenario seed into VRX so wave/wind RNG is
    # deterministic across replays. If the VRX include does not accept a
    # `seed` argument on the cloud box, it will be ignored - then we
    # promote this to whatever VRX actually names the seed (e.g.
    # `random_seed` or `vrx_seed`) in a follow-up.
    vrx_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("vrx_gz"),
                "launch",
                "competition.launch.py",
            ])
        ),
        launch_arguments={
            "world": "sydney_regatta",
            "headless": "True",
            "sim_mode": "full",
            "bridge_competition_topics": "True",
            "competition_mode": "False",
            "name": "wamv",
            "model": "wam-v",
            "seed": LaunchConfiguration("seed"),
        }.items(),
    )

    # Bridge Gazebo's world dynamic-pose stream into ROS as TFMessage.
    # This is the canonical source of WAM-V's world pose; VRX does not
    # bridge this by default in competition.launch.py. The gz topic
    # publishes Pose_V containing every world entity (buoys, terrain,
    # WAM-V, etc.); the adapter below filters for `target_frame`.
    world_pose_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ssv_world_pose_bridge",
        output="screen",
        arguments=[
            "/world/sydney_regatta/dynamic_pose/info"
            "@tf2_msgs/msg/TFMessage"
            "[gz.msgs.Pose_V",
        ],
        remappings=[
            ("/world/sydney_regatta/dynamic_pose/info", "/ssv/world_pose_raw"),
        ],
    )

    state_adapter = Node(
        package="poseidon_ssv_sim",
        executable="ssv_state_adapter",
        name="ssv_state_adapter",
        output="screen",
        parameters=[{
            "input_topic": "/ssv/world_pose_raw",
            "output_topic": "/ssv/state",
            "frame_id": "map",
            "child_frame_id": "ssv/base_link",
            "target_frame": "wamv",
        }],
    )

    contract_shim = Node(
        package="poseidon_ssv_sim",
        executable="ssv_contract_shim",
        name="ssv_contract_shim",
        output="screen",
        parameters=[{
            "clock_rate_hz": 50.0,
            "health_rate_hz": 2.0,
        }],
    )

    imu_relay = Node(
        package="topic_tools",
        executable="relay",
        name="ssv_imu_relay",
        output="screen",
        arguments=[
            "/wamv/sensors/imu/imu/data",
            "/ssv/sensors/imu",
        ],
    )

    gnss_relay = Node(
        package="topic_tools",
        executable="relay",
        name="ssv_gnss_relay",
        output="screen",
        arguments=[
            "/wamv/sensors/gps/gps/fix",
            "/ssv/sensors/gnss",
        ],
    )

    lidar_scan_relay = Node(
        package="topic_tools",
        executable="relay",
        name="ssv_lidar_scan_relay",
        output="screen",
        arguments=[
            "/wamv/sensors/lidars/lidar_wamv_sensor/scan",
            "/ssv/sensors/lidar/scan",
        ],
    )

    lidar_points_relay = Node(
        package="topic_tools",
        executable="relay",
        name="ssv_lidar_points_relay",
        output="screen",
        arguments=[
            "/wamv/sensors/lidars/lidar_wamv_sensor/points",
            "/ssv/sensors/lidar/points",
        ],
    )

    # TODO(ssv): bridge /ssv/thruster_cmd and /ssv/rudder_cmd into VRX
    # controls (blocked on actuator schema ADR; see SYSTEM_DESIGN.md
    # Section 14 and PR #4 deferrals).
    # TODO(ssv): remap remaining VRX sensors under /ssv/sensors/* as needed.
    # TODO(ssv): disable/bypass native VRX wave forcing so env-service
    # remains the single ocean truth source.

    return LaunchDescription([
        declare_seed,
        banner,
        vrx_launch,
        world_pose_bridge,
        state_adapter,
        contract_shim,
        imu_relay,
        gnss_relay,
        lidar_scan_relay,
        lidar_points_relay,
    ])
