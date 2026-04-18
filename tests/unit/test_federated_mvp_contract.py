from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_compose_declares_federated_core_services() -> None:
    compose = _read("deploy/compose/docker-compose.yml")
    for service in ("sim-auv:", "sim-ssv:", "federation-bridge:", "scenario-engine:", "env-service:"):
        assert service in compose


def test_compose_wires_federated_topic_publishers() -> None:
    compose = _read("deploy/compose/docker-compose.yml")
    assert "mock_auv_runtime.py" in compose
    assert "mock_ssv_runtime.py" in compose
    assert "federation_bridge.py" in compose
    assert "run_scenario_mvp.py" in compose


def test_verify_script_checks_mvp_topics() -> None:
    script = _read("tools/verify-backbone-t1.sh")
    for topic in ("/auv/state", "/ssv/state", "/scenario/clock"):
        assert topic in script
    assert "federated compose services publish" in script


def test_system_design_declares_dual_runtime_and_federation_topics() -> None:
    design = _read("SYSTEM_DESIGN.md")
    for phrase in ("Gazebo runtime A (DAVE)", "Gazebo runtime B (VRX)", "/federation/runtime_health", "/scenario/clock"):
        assert phrase in design
