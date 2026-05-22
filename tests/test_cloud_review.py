from __future__ import annotations

from datetime import date

from assistant_core.execution import cloud_review
from assistant_core.schemas import CloudCandidate, FileExecutionRecord


def test_estimate_cloud_cost_uses_configured_rates():
    cost = cloud_review.estimate_cloud_cost_usd(
        prompt_tokens=1000,
        completion_tokens=2000,
        pricing={
            "cloud-claude-opus": {
                "input_per_1k_usd": 0.01,
                "output_per_1k_usd": 0.02,
            }
        },
    )

    assert cost == 0.05


def test_run_cloud_review_call_writes_response_and_costs(tmp_path, monkeypatch):
    from tests.test_execution_steps import _cfg

    cfg = _cfg(tmp_path)
    cfg.cloud_fallback_enabled = True
    cfg.cloud_model_pricing = {
        "cloud-claude-opus": {
            "input_per_1k_usd": 0.01,
            "output_per_1k_usd": 0.02,
        }
    }
    record = FileExecutionRecord(
        file_path=str(tmp_path / "LocalAI/inbox/cloud_review/example.md"),
        needs_cloud_review=True,
    )
    candidate = CloudCandidate(file_path=record.file_path, reason="test", gate_passed=True)

    monkeypatch.setattr(
        cloud_review.litellm_client,
        "chat_completion",
        lambda *args, **kwargs: "cloud review response",
    )

    updated, spent = cloud_review.run_cloud_review_call(
        cfg=cfg,
        record=record,
        candidate=candidate,
        day=date(2026, 5, 18),
        spent_so_far_usd=0.0,
        mode="NIGHT_MODE",
        manual_override=False,
    )

    assert updated.escalated is True
    assert updated.cloud_response_chars == len("cloud review response")
    assert updated.estimated_cost_usd is not None
    assert spent == updated.estimated_cost_usd
    assert updated.cloud_response_path is not None
    assert "cloud review response" in open(updated.cloud_response_path, encoding="utf-8").read()
    assert record.escalated_to_cloud is True


def test_run_cloud_review_call_blocks_when_budget_would_be_exceeded(tmp_path, monkeypatch):
    from tests.test_execution_steps import _cfg

    cfg = _cfg(tmp_path)
    cfg.daily_cloud_budget_usd = 0.000001
    record = FileExecutionRecord(
        file_path=str(tmp_path / "LocalAI/inbox/cloud_review/example.md"),
        needs_cloud_review=True,
    )
    candidate = CloudCandidate(file_path=record.file_path, reason="test", gate_passed=True)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LiteLLM should not be called after budget preflight fails")

    monkeypatch.setattr(cloud_review.litellm_client, "chat_completion", fail_if_called)

    updated, spent = cloud_review.run_cloud_review_call(
        cfg=cfg,
        record=record,
        candidate=candidate,
        day=date(2026, 5, 18),
        spent_so_far_usd=0.0,
        mode="NIGHT_MODE",
        manual_override=False,
    )

    assert updated.escalated is False
    assert updated.gate_passed is False
    assert updated.gate_block_reason == "budget exceeded"
    assert spent == 0.0
