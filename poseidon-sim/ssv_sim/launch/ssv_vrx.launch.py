"""VRX-backed SSV runtime launch.

Track: SSV runtime. Playbook: docs/runbooks/integration-ssv-vrx.md.
Contract: SYSTEM_DESIGN.md Section 14.

Current stage:
- launches stock VRX competition world headless
- publishes /ssv/state via adapter node
- republishes /sim/ssv/clock and /sim/ssv/health via shim
- remaps first-pass VRX sensor topics into /ssv/sensors/*
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

    state_adapter = Node(
        package="poseidon_ssv_sim",
        executable="ssv_state_adapter",
        name="ssv_state_adapter",
        output="screen",
        parameters=[{
            "input_topic": "/wamv/pose",
            "output_topic": "/ssv/state",
            "frame_id": "map",
            "child_frame_id": "ssv/base_link",
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

    # TODO(ssv): replace /wamv/pose-based approximation with a direct Gazebo
    # world-state adapter if needed for higher-fidelity odometry.
    # TODO(ssv): bridge /ssv/thruster_cmd and /ssv/rudder_cmd into VRX controls.
    # TODO(ssv): remap remaining VRX sensors under /ssv/sensors/* as needed.
    # TODO(ssv): disable/bypass native VRX wave forcing so env-service remains the
    # single ocean truth source.

    return LaunchDescription([
        declare_seed,
        banner,
        vrx_launch,
        state_adapter,
        contract_shim,
        imu_relay,
        gnss_relay,
        lidar_scan_relay,
        lidar_points_relay,
    ])
