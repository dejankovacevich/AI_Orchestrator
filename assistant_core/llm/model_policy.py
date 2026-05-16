from __future__ import annotations

import os
from pathlib import Path

from assistant_core.safety import assert_cloud_allowed, assert_model_allowed


LOCAL_ESCALATION = {
    "general": ["local-main", "local-secondary", "local-reasoner"],
    "coding": ["local-coder", "local-main", "local-secondary"],
    "reasoning_check": ["local-reasoner", "local-main"],
}


def local_model_chain(task_type: str) -> list[str]:
    return LOCAL_ESCALATION.get(task_type, LOCAL_ESCALATION["general"])


def assert_model_group_allowed(model_group: str, mode: str, *, manual_override: bool = False) -> None:
    assert_model_allowed(model_group, mode, manual_override=manual_override)


def authorize_cloud_claude(
    *,
    file_path: str | Path,
    cloud_fallback_enabled: bool,
    work_packet_cloud_allowed: bool,
    high_stakes: bool,
    local_quality_gate_failed: bool,
    daily_budget_remaining: bool,
    cloud_review_dir: str | Path,
) -> None:
    assert_cloud_allowed(
        file_path=file_path,
        cloud_fallback_enabled=cloud_fallback_enabled,
        work_packet_cloud_allowed=work_packet_cloud_allowed,
        high_stakes=high_stakes,
        local_quality_gate_failed=local_quality_gate_failed,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        daily_budget_remaining=daily_budget_remaining,
        cloud_review_dir=cloud_review_dir,
    )
