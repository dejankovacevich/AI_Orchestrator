from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from assistant_core.config_writer import (
    ConfigEditError,
    update_assistant_config,
)


def _write_minimal_config(path: Path, **overrides) -> None:
    base = {
        "local_ai_root": "~/LocalAI",
        "inbox_dir": "~/LocalAI/inbox",
        "output_dir": "~/LocalAI/output",
        "archive_dir": "~/LocalAI/archive",
        "log_dir": "~/LocalAI/logs",
        "work_packets_dir": "~/LocalAI/work_packets",
        "obsidian_vault_dir": "~/Obsidian/LocalAI-ChiefOfStaff",
        "ollama_base_url": "http://localhost:11434",
        "litellm_base_url": "http://localhost:4000",
        "temporal_address": "localhost:7233",
        "postgres_url": "postgresql://localai:localai@localhost:5432/localai",
        "day_mode_start": "07:30",
        "night_mode_start": "01:30",
        "night_mode_end": "07:00",
        "extra_setting": "preserve me",
    }
    base.update(overrides)
    path.write_text(yaml.safe_dump(base, sort_keys=False), encoding="utf-8")


def test_updates_allowed_fields_and_preserves_others(tmp_path):
    config_path = tmp_path / "assistant.yaml"
    _write_minimal_config(config_path)

    result = update_assistant_config(
        {
            "day_mode_start": "08:00",
            "night_mode_start": "23:30",
        },
        path=config_path,
    )

    assert result["day_mode_start"] == "08:00"
    assert result["night_mode_start"] == "23:30"
    assert result["extra_setting"] == "preserve me"

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert loaded["day_mode_start"] == "08:00"
    assert loaded["night_mode_start"] == "23:30"
    assert loaded["extra_setting"] == "preserve me"
    assert loaded["night_mode_end"] == "07:00"


def test_rejects_fields_outside_allow_list(tmp_path):
    config_path = tmp_path / "assistant.yaml"
    _write_minimal_config(config_path)

    with pytest.raises(ConfigEditError, match="allow-list"):
        update_assistant_config(
            {
                "day_mode_start": "08:00",
                "cloud_fallback_enabled": True,
            },
            path=config_path,
        )

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert loaded["day_mode_start"] == "07:30"


@pytest.mark.parametrize(
    "bad_value",
    ["8:00", "08:60", "24:00", "08", "08-00", "", "abc"],
)
def test_rejects_malformed_time(tmp_path, bad_value):
    config_path = tmp_path / "assistant.yaml"
    _write_minimal_config(config_path)

    with pytest.raises(ConfigEditError, match="HH:MM"):
        update_assistant_config({"day_mode_start": bad_value}, path=config_path)


@pytest.mark.parametrize("good_value", ["00:00", "07:30", "23:59", "12:00", "01:30"])
def test_accepts_valid_time_strings(tmp_path, good_value):
    config_path = tmp_path / "assistant.yaml"
    _write_minimal_config(config_path)

    update_assistant_config({"day_mode_start": good_value}, path=config_path)

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert loaded["day_mode_start"] == good_value


def test_write_is_atomic_via_temp_file(tmp_path):
    config_path = tmp_path / "assistant.yaml"
    _write_minimal_config(config_path)

    update_assistant_config({"night_mode_end": "06:30"}, path=config_path)

    leftovers = [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


def test_rejects_when_config_missing(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigEditError, match="does not exist"):
        update_assistant_config({"day_mode_start": "08:00"}, path=missing)
