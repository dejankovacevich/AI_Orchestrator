from __future__ import annotations

from datetime import time
from pathlib import Path
from unittest.mock import patch

import pytest

from assistant_core import scheduler_status
from assistant_core.config import AssistantConfig


def _make_cfg(**overrides) -> AssistantConfig:
    base: dict[str, object] = {
        "local_ai_root": Path("/tmp/localai"),
        "inbox_dir": Path("/tmp/localai/inbox"),
        "output_dir": Path("/tmp/localai/output"),
        "archive_dir": Path("/tmp/localai/archive"),
        "log_dir": Path("/tmp/localai/logs"),
        "work_packets_dir": Path("/tmp/localai/work_packets"),
        "obsidian_vault_dir": Path("/tmp/obsidian"),
        "ollama_base_url": "http://localhost:11434",
        "litellm_base_url": "http://localhost:4000",
        "temporal_address": "localhost:7233",
        "postgres_url": "postgresql://localai:localai@localhost:5432/localai",
        "day_mode_start": "07:30",
        "night_mode_start": "01:30",
        "night_mode_end": "07:00",
    }
    base.update(overrides)
    return AssistantConfig.model_validate(base)


def test_day_window_normal_case_morning():
    cfg = _make_cfg()
    window = scheduler_status.compute_window_status(time(10, 0), cfg)
    assert window.in_day is True
    assert window.in_night is False
    assert window.label == "DAY window"


def test_night_window_wraps_over_midnight_at_02_00():
    cfg = _make_cfg()
    window = scheduler_status.compute_window_status(time(2, 0), cfg)
    assert window.in_night is True
    assert window.in_day is False
    assert window.label == "NIGHT window"


def test_night_window_inclusive_at_start_exclusive_at_end():
    cfg = _make_cfg()
    assert scheduler_status.compute_window_status(time(1, 30), cfg).in_night is True
    assert scheduler_status.compute_window_status(time(7, 0), cfg).in_night is False


def test_day_window_inclusive_at_start_exclusive_at_night_start():
    cfg = _make_cfg()
    assert scheduler_status.compute_window_status(time(7, 30), cfg).in_day is True
    assert scheduler_status.compute_window_status(time(1, 30), cfg).in_day is False


def test_between_windows_when_neither_match():
    cfg = _make_cfg(day_mode_start="08:00", night_mode_start="22:00", night_mode_end="07:00")
    window = scheduler_status.compute_window_status(time(7, 30), cfg)
    assert window.in_day is False
    assert window.in_night is False
    assert window.label == "between windows"


@pytest.mark.parametrize(
    "now, day_start, night_start, night_end, expect_in_day, expect_in_night",
    [
        # mid-morning is squarely day
        (time(9, 0), "07:30", "01:30", "07:00", True, False),
        # day wraps over midnight: 00:30 is still in [07:30, 01:30)
        (time(0, 30), "07:30", "01:30", "07:00", True, False),
        # night window
        (time(3, 0), "07:30", "01:30", "07:00", False, True),
        # transition gap 07:00 -> 07:30: neither
        (time(7, 0), "07:30", "01:30", "07:00", False, False),
        # day starts inclusive
        (time(7, 30), "07:30", "01:30", "07:00", True, False),
    ],
)
def test_window_table(now, day_start, night_start, night_end, expect_in_day, expect_in_night):
    cfg = _make_cfg(
        day_mode_start=day_start,
        night_mode_start=night_start,
        night_mode_end=night_end,
    )
    window = scheduler_status.compute_window_status(now, cfg)
    assert window.in_day is expect_in_day
    assert window.in_night is expect_in_night


def test_launchd_job_loaded_true_when_label_present_in_output(monkeypatch):
    class FakeCompleted:
        stdout = "PID\tStatus\tLabel\n123\t0\tcom.localai.orchestrator.nightly\n"

    monkeypatch.setattr(
        scheduler_status.subprocess,
        "run",
        lambda *args, **kwargs: FakeCompleted(),
    )
    assert scheduler_status.launchd_job_loaded() is True


def test_launchd_job_loaded_false_when_label_absent(monkeypatch):
    class FakeCompleted:
        stdout = "PID\tStatus\tLabel\n123\t0\tcom.apple.something\n"

    monkeypatch.setattr(
        scheduler_status.subprocess,
        "run",
        lambda *args, **kwargs: FakeCompleted(),
    )
    assert scheduler_status.launchd_job_loaded() is False


def test_launchd_plist_installed_uses_supplied_dir(tmp_path):
    target = tmp_path / "com.localai.orchestrator.nightly.plist"
    assert scheduler_status.launchd_plist_installed(tmp_path) is False
    target.write_text("<plist/>", encoding="utf-8")
    assert scheduler_status.launchd_plist_installed(tmp_path) is True


def test_auto_execution_status_dict_keys():
    with patch.object(scheduler_status, "launchd_job_loaded", return_value=False), patch.object(
        scheduler_status, "launchd_plist_installed", return_value=False
    ), patch.object(scheduler_status, "project_plist_exists", return_value=True):
        snapshot = scheduler_status.auto_execution_status()
    assert snapshot == {
        "loaded_in_launchctl": False,
        "installed_in_launch_agents": False,
        "project_plist_present": True,
    }


def test_port_open_true_when_socket_connects():
    with patch.object(scheduler_status.socket, "create_connection", return_value=type("S", (), {"__enter__": lambda self: self, "__exit__": lambda *a: None})()):
        assert scheduler_status.port_open("127.0.0.1", 5432) is True


def test_port_open_false_when_socket_raises():
    with patch.object(
        scheduler_status.socket,
        "create_connection",
        side_effect=OSError("nope"),
    ):
        assert scheduler_status.port_open("127.0.0.1", 5432) is False
