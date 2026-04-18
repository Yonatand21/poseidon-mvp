"""VRX SSV runtime launch skeleton.

Track: SSV runtime. Playbook: docs/runbooks/integration-ssv-vrx.md.
Contract: SYSTEM_DESIGN.md Section 14.

Replace the TODO sections with real VRX launch and topic remaps. The
federated MVP only requires the topic contract to be honored; the
underlying physics can evolve freely as long as the contract is stable.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description() -> LaunchDescription:
    declare_seed = DeclareLaunchArgument(
        "seed",
        default_value="42",
        description="Deterministic seed propagated to scenario engine and federation bridge.",
    )

    # TODO(ssv): include the VRX world launch here. Typical pattern:
    #   IncludeLaunchDescription(
    #       PythonLaunchDescriptionSource(
    #           os.path.join(get_package_share_directory("vrx_gz"),
    #                        "launch", "competition.launch.py")
    #       ),
    #       launch_arguments={"world": "sydney_regatta"}.items(),
    #   )

    # TODO(ssv): spawn WAM-V and remap its default odometry / sensor
    # topics -> /ssv/state and /ssv/sensors/*. Example:
    #   Node(
    #       package="vrx_gz",
    #       executable="spawn_wamv",
    #       remappings=[
    #           ("/wamv/sensors/position/navsat", "/ssv/sensors/gnss"),
    #           ("/wamv/sensors/imu/imu",         "/ssv/sensors/imu"),
    #           ("/wamv/odom",                    "/ssv/state"),
    #       ],
    #   )

    # TODO(ssv): add a small clock/health shim publishing /sim/ssv/clock
    # and /sim/ssv/health so the federation bridge can sync. Reference
    # pattern is the mock in
    # poseidon-sim/ssv_sim/src/mock_ssv_runtime.py.

    banner = LogInfo(msg=[
        "ssv_vrx.launch.py skeleton - seed=", LaunchConfiguration("seed"),
        " - replace TODO sections with VRX launch and remaps.",
    ])

    return LaunchDescription([
        declare_seed,
        banner,
    ])
