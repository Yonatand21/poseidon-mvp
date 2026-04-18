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

    declare_world_name = DeclareLaunchArgument(
        "world_name",
        default_value="dave_ocean_waves.world",
        description="Planned DAVE world name for future AUV runtime integration.",
    )

    declare_vehicle_name = DeclareLaunchArgument(
        "vehicle_name",
        default_value="rexrov",
        description="Planned stock AUV model name for future DAVE integration.",
    )

    declare_use_mock_backend = DeclareLaunchArgument(
        "use_mock_backend",
        default_value="true",
        description="Keep Mac-safe mock backend enabled during prep/wiring phase.",
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

    runtime_actions = [
        # Future DAVE include/spawn/shim actions will be appended here.
        # Keep empty during the Mac-safe prep/wiring phase.
        #
        # Planned action order:
        # 1. Include DAVE world launch
        # 2. Spawn stock AUV and remap native topics into /auv/state and /auv/sensors/*
        # 3. Add a small shim that publishes /sim/auv/clock and /sim/auv/health
        #    for the federation bridge, matching the mock_auv_runtime.py contract
    ]

    banner = LogInfo(msg=[
        "auv_dave.launch.py skeleton - seed=", LaunchConfiguration("seed"),
        " world_name=", LaunchConfiguration("world_name"),
        " vehicle_name=", LaunchConfiguration("vehicle_name"),
        " use_mock_backend=", LaunchConfiguration("use_mock_backend"),
        " - replace TODO sections with DAVE launch and remaps.",
    ])

    return LaunchDescription([
        declare_seed,
        declare_world_name,
        declare_vehicle_name,
        declare_use_mock_backend,
        *runtime_actions,
        banner,
    ])
