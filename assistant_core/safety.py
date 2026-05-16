from __future__ import annotations

import os
from pathlib import Path

from assistant_core.paths import is_relative_to, resolve_user_path


LOCAL_MODEL_GROUPS = frozenset(
    {"local-main", "local-secondary", "local-coder", "local-reasoner"}
)

DAY_UNLOCK_FLAG_NAME = "day_unlock.flag"
DAY_UNLOCK_ENV_VAR = "LOCALAI_DAY_UNLOCK"
DEFAULT_STATE_DIR = Path("~/LocalAI/state").expanduser()
_TRUTHY = {"1", "true", "yes", "on"}


class SafetyError(RuntimeError):
    """Raised when a requested action violates the local-first safety policy."""


def assert_cloud_allowed(
    *,
    file_path: str | Path,
    cloud_fallback_enabled: bool,
    work_packet_cloud_allowed: bool,
    high_stakes: bool,
    local_quality_gate_failed: bool,
    anthropic_api_key: str | None,
    daily_budget_remaining: bool,
    cloud_review_dir: str | Path,
) -> None:
    target = resolve_user_path(file_path)
    review_dir = resolve_user_path(cloud_review_dir)
    in_review_dir = is_relative_to(target, review_dir)
    marked_cloud = ".cloud." in target.name

    if not cloud_fallback_enabled:
        raise SafetyError("Cloud fallback is disabled by configuration.")
    if not work_packet_cloud_allowed:
        raise SafetyError("Work packet does not explicitly allow cloud fallback.")
    if not (in_review_dir or marked_cloud):
        raise SafetyError("Cloud review requires file inside cloud_review or filename containing .cloud.")
    if not anthropic_api_key:
        raise SafetyError("ANTHROPIC_API_KEY is not present.")
    if not (high_stakes or local_quality_gate_failed):
        raise SafetyError("Cloud review requires high-stakes work or failed local quality gates.")
    if not daily_budget_remaining:
        raise SafetyError("Daily cloud budget has been exceeded.")


def assert_no_external_write(action: str, allowed: bool = False) -> None:
    if not allowed:
        raise SafetyError(f"External write blocked in v1: {action}")


def assert_original_file_write_allowed(target: str | Path, allowed_write_roots: list[str | Path]) -> None:
    resolved = resolve_user_path(target)
    roots = [resolve_user_path(root) for root in allowed_write_roots]
    if not any(is_relative_to(resolved, root) for root in roots):
        raise SafetyError(f"Original file modification blocked for {resolved}")


def day_unlock_active(state_dir: str | Path | None = None) -> bool:
    """Return True when the day-unlock override is active.

    Active if either:
    - environment variable ``LOCALAI_DAY_UNLOCK`` is set to a truthy value
      (1, true, yes, on — case-insensitive), or
    - the sentinel file ``<state_dir>/day_unlock.flag`` exists.

    Both checks are intentional: env var = per-shell quick unlock,
    sentinel file = persistent unlock visible via ``ls``.
    """
    if os.environ.get(DAY_UNLOCK_ENV_VAR, "").strip().lower() in _TRUTHY:
        return True
    base = Path(state_dir).expanduser() if state_dir is not None else DEFAULT_STATE_DIR
    return (base / DAY_UNLOCK_FLAG_NAME).exists()


def day_unlock_flag_path(state_dir: str | Path | None = None) -> Path:
    """Return the configured path of the day-unlock sentinel file."""
    base = Path(state_dir).expanduser() if state_dir is not None else DEFAULT_STATE_DIR
    return base / DAY_UNLOCK_FLAG_NAME


def assert_heavy_execution_allowed(
    mode: str,
    *,
    manual_override: bool = False,
    state_dir: str | Path | None = None,
) -> None:
    normalized = mode.upper()
    effective_override = manual_override or day_unlock_active(state_dir)
    if normalized == "DAY_MODE" and not effective_override:
        raise SafetyError("Local model execution is blocked in DAY_MODE without explicit manual override.")
    if normalized not in {"DAY_MODE", "NIGHT_MODE", "MANUAL_RESUME"}:
        raise SafetyError(f"Unknown execution mode: {mode}")


def assert_model_allowed(
    model_group: str,
    mode: str,
    *,
    manual_override: bool = False,
    state_dir: str | Path | None = None,
) -> None:
    if model_group == "cloud-claude-opus":
        raise SafetyError("Claude must be authorized through cloud policy checks, not model selection alone.")
    if model_group in LOCAL_MODEL_GROUPS:
        assert_heavy_execution_allowed(
            mode, manual_override=manual_override, state_dir=state_dir
        )
