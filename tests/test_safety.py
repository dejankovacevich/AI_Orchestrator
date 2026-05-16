from pathlib import Path

import pytest

from assistant_core.safety import (
    DAY_UNLOCK_ENV_VAR,
    LOCAL_MODEL_GROUPS,
    SafetyError,
    assert_cloud_allowed,
    assert_heavy_execution_allowed,
    assert_model_allowed,
    assert_original_file_write_allowed,
    day_unlock_active,
    day_unlock_flag_path,
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


@pytest.mark.parametrize("model_group", sorted(LOCAL_MODEL_GROUPS))
def test_every_local_model_group_blocked_in_day_mode(model_group):
    with pytest.raises(SafetyError, match="DAY_MODE"):
        assert_model_allowed(model_group, "DAY_MODE", manual_override=False)


@pytest.mark.parametrize("model_group", sorted(LOCAL_MODEL_GROUPS))
def test_local_model_groups_allowed_in_night_mode(model_group):
    assert_model_allowed(model_group, "NIGHT_MODE", manual_override=False)


def test_local_model_allowed_in_day_mode_with_explicit_override():
    assert_model_allowed("local-main", "DAY_MODE", manual_override=True)


def test_cloud_claude_blocked_at_model_selection_layer():
    with pytest.raises(SafetyError, match="cloud policy"):
        assert_model_allowed("cloud-claude-opus", "NIGHT_MODE", manual_override=True)


def test_day_unlock_inactive_by_default(isolate_day_unlock):
    assert day_unlock_active() is False
    assert day_unlock_active(state_dir=isolate_day_unlock) is False


def test_day_unlock_activates_when_flag_file_present(isolate_day_unlock):
    flag = day_unlock_flag_path()
    assert flag.parent == isolate_day_unlock
    flag.write_text("unlocked_at: 2026-05-16T16:00:00Z\nreason: test\n", encoding="utf-8")

    assert day_unlock_active() is True
    assert_model_allowed("local-main", "DAY_MODE", manual_override=False)
    assert_model_allowed("local-secondary", "DAY_MODE", manual_override=False)


def test_day_unlock_activates_via_env_var(monkeypatch, isolate_day_unlock):
    monkeypatch.setenv(DAY_UNLOCK_ENV_VAR, "true")

    assert day_unlock_active() is True
    assert_model_allowed("local-coder", "DAY_MODE", manual_override=False)


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", "  YeS  "])
def test_env_var_truthy_values_enable_unlock(monkeypatch, isolate_day_unlock, value):
    monkeypatch.setenv(DAY_UNLOCK_ENV_VAR, value)
    assert day_unlock_active() is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "random"])
def test_env_var_non_truthy_values_do_not_enable_unlock(monkeypatch, isolate_day_unlock, value):
    monkeypatch.setenv(DAY_UNLOCK_ENV_VAR, value)
    assert day_unlock_active() is False


def test_removing_flag_restores_strict_policy(isolate_day_unlock):
    flag = day_unlock_flag_path()
    flag.write_text("test", encoding="utf-8")
    assert day_unlock_active() is True

    flag.unlink()
    assert day_unlock_active() is False
    with pytest.raises(SafetyError, match="DAY_MODE"):
        assert_model_allowed("local-main", "DAY_MODE", manual_override=False)


def test_day_unlock_does_not_open_cloud_claude(isolate_day_unlock, monkeypatch):
    monkeypatch.setenv(DAY_UNLOCK_ENV_VAR, "true")
    with pytest.raises(SafetyError, match="cloud policy"):
        assert_model_allowed("cloud-claude-opus", "DAY_MODE", manual_override=False)


def test_explicit_state_dir_argument_overrides_default(tmp_path, isolate_day_unlock):
    custom = tmp_path / "elsewhere"
    custom.mkdir()
    (custom / "day_unlock.flag").write_text("scoped", encoding="utf-8")

    assert day_unlock_active() is False
    assert day_unlock_active(state_dir=custom) is True
