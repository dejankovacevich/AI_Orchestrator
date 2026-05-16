from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_generated_litellm_config_is_ignored():
    assert "config/litellm.yaml" in read(".gitignore")


def test_docker_compose_scripts_check_compose_subcommand_before_using_it():
    for script in ["scripts/run_tests.sh", "scripts/start_services.sh", "scripts/stop_services.sh", "scripts/status_services.sh"]:
        text = read(script)
        assert "docker compose version" in text or "docker-compose" in text


def test_launchd_script_requires_explicit_write_to_launch_agents():
    text = read("scripts/create_launchd_plist.sh")

    assert "LOCALAI_WRITE_LAUNCHD" in text
    assert "launchd/com.localai.orchestrator.nightly.plist" in text
