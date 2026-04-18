"""DAVE AUV runtime launch skeleton.

Track: AUV runtime. Playbook: docs/runbooks/integration-auv-dave.md.
Contract: SYSTEM_DESIGN.md Section 14.

Replace the TODO sections with real DAVE launch and topic remaps. The
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

    # TODO(auv): include the DAVE world launch here. Typical pattern:
    #   IncludeLaunchDescription(
    #       PythonLaunchDescriptionSource(
    #           os.path.join(get_package_share_directory("dave_worlds"),
    #                        "launch", "dave_world.launch.py")
    #       ),
    #       launch_arguments={"world_name": "dave_ocean_waves.world"}.items(),
    #   )

    # TODO(auv): spawn a stock AUV (RexROV or LAUV) and remap its default
    # odometry topic -> /auv/state, sensor topics -> /auv/sensors/*.
    # Example using a Node with remappings:
    #   Node(
    #       package="dave_nodes",
    #       executable="spawn_rexrov",
    #       remappings=[
    #           ("/rexrov/odom", "/auv/state"),
    #           ("/rexrov/camera/image_raw", "/auv/sensors/camera/image_raw"),
    #           ("/rexrov/dvl",              "/auv/sensors/dvl"),
    #       ],
    #   )

    # TODO(auv): add a small clock/health shim publishing /sim/auv/clock
    # and /sim/auv/health so the federation bridge can sync against this
    # runtime. Reference pattern is the mock in
    # poseidon-sim/auv_sim/src/mock_auv_runtime.py.

    banner = LogInfo(msg=[
        "auv_dave.launch.py skeleton - seed=", LaunchConfiguration("seed"),
        " - replace TODO sections with DAVE launch and remaps.",
    ])

    return LaunchDescription([
        declare_seed,
        banner,
    ])
