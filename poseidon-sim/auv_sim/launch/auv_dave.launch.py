"""DAVE AUV runtime launch scaffold.

Track: AUV runtime. Playbook: docs/runbooks/integration-auv-dave.md.
Contract: SYSTEM_DESIGN.md Section 14.

Purpose:
- preserve the canonical AUV runtime contract on Mac/arm64
- keep the mock runtime available as the primary fallback
- allow a non-mock launch path that is explicit about being a DAVE-stub path
- keep launch structure ready for eventual Linux/NVIDIA DAVE include/spawn/remap work

Current behavior:
- backend_mode=mock:
    intended for the Mac-safe mock runtime path outside this file's non-mock flow
- backend_mode=dave_stub with use_mock_backend:=false:
    does NOT launch real DAVE
    starts only the federation contract shim
    expects /auv/state to already exist from an upstream runtime source
    publishes /sim/auv/clock and /sim/auv/health for federation compatibility

Deferred to Linux/NVIDIA:
- include real DAVE world launch
- spawn stock AUV
- remap native DAVE topics into:
    /auv/state
    /auv/sensors/*
- bind actuator subscriptions:
    /auv/thruster_cmd
    /auv/fin_cmd
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression


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

    declare_backend_mode = DeclareLaunchArgument(
        "backend_mode",
        default_value="mock",
        description=(
            "AUV backend mode. Current intended values: "
            "mock or dave_stub. "
            "Use dave_stub with use_mock_backend:=false to exercise the "
            "non-mock contract-shim launch path on Mac."
        ),
    )

    declare_state_timeout_sec = DeclareLaunchArgument(
        "state_timeout_sec",
        default_value="1.0",
        description="Seconds before /sim/auv/health flips false when /auv/state goes stale.",
    )

    declare_clock_rate_hz = DeclareLaunchArgument(
        "clock_rate_hz",
        default_value="50.0",
        description="Publish rate for /sim/auv/clock.",
    )

    declare_health_rate_hz = DeclareLaunchArgument(
        "health_rate_hz",
        default_value="2.0",
        description="Publish rate for /sim/auv/health.",
    )

    # Deferred Linux/NVIDIA integration plan:
    #
    # 1. Include real DAVE world launch
    # 2. Spawn stock AUV (RexROV or LAUV)
    # 3. Remap native DAVE topics into the canonical contract:
    #      /auv/state         nav_msgs/Odometry
    #      /auv/sensors/*     sensor outputs
    #      /auv/thruster_cmd  subscribed by runtime
    #      /auv/fin_cmd       subscribed by runtime
    # 4. Keep the shim below for:
    #      /sim/auv/clock
    #      /sim/auv/health
    #
    # This file intentionally does not claim that real DAVE is active on Mac/arm64.

    dave_stub_mode_condition = IfCondition(
        PythonExpression(
            [
                "'",
                LaunchConfiguration("backend_mode"),
                "' == 'dave_stub'",
            ]
        )
    )

    dave_stub_non_mock_condition = IfCondition(
        PythonExpression(
            [
                "'",
                LaunchConfiguration("use_mock_backend"),
                "' == 'false' and '",
                LaunchConfiguration("backend_mode"),
                "' == 'dave_stub'",
            ]
        )
    )

    banner = LogInfo(
        msg=[
            "auv_dave.launch.py - seed=",
            LaunchConfiguration("seed"),
            " world_name=",
            LaunchConfiguration("world_name"),
            " vehicle_name=",
            LaunchConfiguration("vehicle_name"),
            " use_mock_backend=",
            LaunchConfiguration("use_mock_backend"),
            " backend_mode=",
            LaunchConfiguration("backend_mode"),
            " state_timeout_sec=",
            LaunchConfiguration("state_timeout_sec"),
            " clock_rate_hz=",
            LaunchConfiguration("clock_rate_hz"),
            " health_rate_hz=",
            LaunchConfiguration("health_rate_hz"),
        ]
    )

    backend_summary_notice = LogInfo(
        msg=[
            "[auv_dave] use_mock_backend=",
            LaunchConfiguration("use_mock_backend"),
            " backend_mode=",
            LaunchConfiguration("backend_mode"),
        ]
    )

    mock_mode_notice = LogInfo(
        msg="[auv_dave] backend_mode=mock selected",
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("backend_mode"),
                    "' == 'mock'",
                ]
            )
        ),
    )

    dave_stub_notice = LogInfo(
        msg="[auv_dave] backend_mode=dave_stub selected",
        condition=dave_stub_mode_condition,
    )

    non_mock_notice_1 = LogInfo(
        msg="[auv_dave] Mac/arm64 fallback active: real DAVE runtime is not launched in this path",
        condition=dave_stub_non_mock_condition,
    )

    non_mock_notice_2 = LogInfo(
        msg="[auv_dave] starting federation contract shim only; expects /auv/state from an upstream source",
        condition=dave_stub_non_mock_condition,
    )

    non_mock_notice_3 = LogInfo(
        msg="[auv_dave] publishing /sim/auv/clock and /sim/auv/health for federation compatibility",
        condition=dave_stub_non_mock_condition,
    )

    non_mock_notice_4 = LogInfo(
        msg="[auv_dave] TODO(Linux/NVIDIA): include DAVE launch, spawn vehicle, remap native topics to /auv/state and /auv/sensors/*",
        condition=dave_stub_non_mock_condition,
    )

    mode_mismatch_notice = LogInfo(
        msg=(
            "[auv_dave] warning: unsupported combination detected: "
            "use_mock_backend=false with backend_mode!=dave_stub. "
            "On Mac, the supported non-mock path is backend_mode=dave_stub."
        ),
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("use_mock_backend"),
                    "' == 'false' and '",
                    LaunchConfiguration("backend_mode"),
                    "' != 'dave_stub'",
                ]
            )
        ),
    )

    mock_non_mock_conflict_notice = LogInfo(
        msg=(
            "[auv_dave] note: backend_mode=mock does not start the non-mock stub path. "
            "Use backend_mode=dave_stub with use_mock_backend:=false for the Mac shim path."
        ),
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("use_mock_backend"),
                    "' == 'false' and '",
                    LaunchConfiguration("backend_mode"),
                    "' == 'mock'",
                ]
            )
        ),
    )

    shim_process = ExecuteProcess(
        cmd=[
            "python3",
            "/workspace/poseidon-sim/auv_sim/src/auv_clock_health_shim.py",
            "--ros-args",
            "-p",
            ["state_timeout_sec:=", LaunchConfiguration("state_timeout_sec")],
            "-p",
            ["clock_rate_hz:=", LaunchConfiguration("clock_rate_hz")],
            "-p",
            ["health_rate_hz:=", LaunchConfiguration("health_rate_hz")],
        ],
        name="auv_clock_health_shim",
        condition=dave_stub_non_mock_condition,
        output="screen",
    )

    runtime_actions = [
        mock_mode_notice,
        dave_stub_notice,
        mode_mismatch_notice,
        mock_non_mock_conflict_notice,
        non_mock_notice_1,
        non_mock_notice_2,
        non_mock_notice_3,
        non_mock_notice_4,
        shim_process,
    ]

    return LaunchDescription(
        [
            declare_seed,
            declare_world_name,
            declare_vehicle_name,
            declare_use_mock_backend,
            declare_backend_mode,
            declare_state_timeout_sec,
            declare_clock_rate_hz,
            declare_health_rate_hz,
            banner,
            backend_summary_notice,
            *runtime_actions,
        ]
    )
