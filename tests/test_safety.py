from pathlib import Path

import pytest

from assistant_core.safety import (
    SafetyError,
    assert_cloud_allowed,
    assert_heavy_execution_allowed,
    assert_original_file_write_allowed,
)


def test_cloud_blocked_by_default(tmp_path):
    target = tmp_path / "cloud_review" / "brief.cloud.md"
    target.parent.mkdir()
    target.write_text("review me", encoding="utf-8")

    with pytest.raises(SafetyError, match="disabled"):
        assert_cloud_allowed(
            file_path=target,
            cloud_fallback_enabled=False,
            work_packet_cloud_allowed=True,
            high_stakes=True,
            local_quality_gate_failed=True,
            anthropic_api_key="secret",
            daily_budget_remaining=True,
            cloud_review_dir=target.parent,
        )


def test_cloud_blocked_when_file_not_in_review_location(tmp_path):
    target = tmp_path / "notes" / "brief.md"
    review_dir = tmp_path / "cloud_review"
    target.parent.mkdir()
    review_dir.mkdir()
    target.write_text("review me", encoding="utf-8")

    with pytest.raises(SafetyError, match="cloud_review"):
        assert_cloud_allowed(
            file_path=target,
            cloud_fallback_enabled=True,
            work_packet_cloud_allowed=True,
            high_stakes=True,
            local_quality_gate_failed=True,
            anthropic_api_key="secret",
            daily_budget_remaining=True,
            cloud_review_dir=review_dir,
        )


def test_original_file_modification_blocked(tmp_path):
    original = tmp_path / "inbox" / "source.md"
    original.parent.mkdir()
    original.write_text("source", encoding="utf-8")

    with pytest.raises(SafetyError, match="Original file modification"):
        assert_original_file_write_allowed(original, [tmp_path / "output"])


def test_daytime_heavy_execution_blocked_by_default():
    with pytest.raises(SafetyError, match="DAY_MODE"):
        assert_heavy_execution_allowed("DAY_MODE", manual_override=False)
