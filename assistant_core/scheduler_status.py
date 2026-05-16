"""Read-only inspection of the orchestrator's schedule and service health.

This module never modifies launchd, cron, or any running process. It only
reports what is currently true so the control panel and CLI can show clear
status. Modifying the schedule remains a deliberate terminal gesture
(see scripts/create_launchd_plist.sh and the docs/auto_execution.md guide).
"""

from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path

from assistant_core.config import AssistantConfig, load_assistant_config


LAUNCHD_JOB_LABEL = "com.localai.orchestrator.nightly"
LAUNCH_AGENTS_DIR = Path("~/Library/LaunchAgents").expanduser()
PROJECT_PLIST_RELATIVE = Path("launchd") / f"{LAUNCHD_JOB_LABEL}.plist"


@dataclass(frozen=True)
class WindowStatus:
    """Whether ``now`` falls in the configured day or night window."""

    now: time
    day_start: time
    night_start: time
    night_end: time
    in_day: bool
    in_night: bool

    @property
    def label(self) -> str:
        if self.in_night:
            return "NIGHT window"
        if self.in_day:
            return "DAY window"
        return "between windows"


def _parse_time(value: str) -> time:
    hour_str, minute_str = value.split(":", 1)
    return time(hour=int(hour_str), minute=int(minute_str))


def compute_window_status(now: time | None = None, cfg: AssistantConfig | None = None) -> WindowStatus:
    """Return whether the current clock-time is in the day or night window.

    The day window is inclusive of ``day_mode_start`` and exclusive of
    ``night_mode_start``. The night window is inclusive of
    ``night_mode_start`` and exclusive of ``night_mode_end``; it can wrap
    over midnight when ``night_mode_start > night_mode_end``.
    """
    cfg = cfg or load_assistant_config()
    now = now or datetime.now().time()
    day_start = _parse_time(cfg.day_mode_start)
    night_start = _parse_time(cfg.night_mode_start)
    night_end = _parse_time(cfg.night_mode_end)

    in_night = _time_in_range(now, night_start, night_end)
    in_day = (not in_night) and _time_in_range(now, day_start, night_start)
    return WindowStatus(
        now=now,
        day_start=day_start,
        night_start=night_start,
        night_end=night_end,
        in_day=in_day,
        in_night=in_night,
    )


def _time_in_range(now: time, start: time, end: time) -> bool:
    """Return True when ``now`` is in [start, end). Wraps over midnight."""
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


def launchd_job_loaded() -> bool:
    """Return True when launchctl has the nightly job loaded."""
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
    return LAUNCHD_JOB_LABEL in (result.stdout or "")


def launchd_plist_installed(launch_agents_dir: Path | None = None) -> bool:
    """Return True when the plist is installed in ~/Library/LaunchAgents."""
    base = launch_agents_dir or LAUNCH_AGENTS_DIR
    return (base / f"{LAUNCHD_JOB_LABEL}.plist").exists()


def project_plist_exists(project_root: Path | None = None) -> bool:
    """Return True when the project-local plist file has been generated."""
    base = project_root or _project_root()
    return (base / PROJECT_PLIST_RELATIVE).exists()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Quick TCP probe for service health (no protocol-level handshake)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ollama_up(cfg: AssistantConfig | None = None) -> bool:
    cfg = cfg or load_assistant_config()
    host, port = _host_port(cfg.ollama_base_url, default_port=11434)
    return port_open(host, port)


def litellm_up(cfg: AssistantConfig | None = None) -> bool:
    cfg = cfg or load_assistant_config()
    host, port = _host_port(cfg.litellm_base_url, default_port=4000)
    return port_open(host, port)


def temporal_up(cfg: AssistantConfig | None = None) -> bool:
    cfg = cfg or load_assistant_config()
    host, port = _split_host_port(cfg.temporal_address, default_port=7233)
    return port_open(host, port)


def postgres_up(cfg: AssistantConfig | None = None) -> bool:
    cfg = cfg or load_assistant_config()
    host, port = _postgres_host_port(cfg.postgres_url)
    return port_open(host, port)


def _host_port(url: str, *, default_port: int) -> tuple[str, int]:
    rest = url.split("://", 1)[1] if "://" in url else url
    host_port = rest.split("/", 1)[0]
    return _split_host_port(host_port, default_port=default_port)


def _split_host_port(host_port: str, *, default_port: int) -> tuple[str, int]:
    if ":" in host_port:
        host, port_text = host_port.split(":", 1)
        return host or "127.0.0.1", int(port_text)
    return host_port or "127.0.0.1", default_port


def _postgres_host_port(url: str) -> tuple[str, int]:
    rest = url.split("@", 1)[1] if "@" in url else url
    rest = rest.split("/", 1)[0]
    return _split_host_port(rest, default_port=5432)


def auto_execution_status() -> dict[str, bool]:
    """Return a dict reporting the three layers of the nightly schedule."""
    return {
        "loaded_in_launchctl": launchd_job_loaded(),
        "installed_in_launch_agents": launchd_plist_installed(),
        "project_plist_present": project_plist_exists(),
    }


__all__ = [
    "WindowStatus",
    "LAUNCHD_JOB_LABEL",
    "LAUNCH_AGENTS_DIR",
    "PROJECT_PLIST_RELATIVE",
    "auto_execution_status",
    "compute_window_status",
    "launchd_job_loaded",
    "launchd_plist_installed",
    "project_plist_exists",
    "ollama_up",
    "litellm_up",
    "temporal_up",
    "postgres_up",
    "port_open",
]
