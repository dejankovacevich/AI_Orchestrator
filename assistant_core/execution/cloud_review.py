from __future__ import annotations

from pathlib import Path
from typing import Any

from assistant_core.config import AssistantConfig
from assistant_core.execution.output_writer import dated_output_dir
from assistant_core.llm import litellm_client
from assistant_core.schemas import CloudCandidate, FileExecutionRecord

CLOUD_MODEL_GROUP = "cloud-claude-opus"
DEFAULT_CLOUD_INPUT_RATE_PER_1K = 0.015
DEFAULT_CLOUD_OUTPUT_RATE_PER_1K = 0.075


def estimate_cloud_cost_usd(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    pricing: dict[str, Any] | None,
    model_group: str = CLOUD_MODEL_GROUP,
) -> float:
    """Estimate cloud call cost from token counts and per-model pricing."""
    model_pricing = (pricing or {}).get(model_group, {})
    input_rate = float(
        model_pricing.get("input_per_1k_usd", DEFAULT_CLOUD_INPUT_RATE_PER_1K)
    )
    output_rate = float(
        model_pricing.get("output_per_1k_usd", DEFAULT_CLOUD_OUTPUT_RATE_PER_1K)
    )
    return (prompt_tokens / 1000.0 * input_rate) + (
        completion_tokens / 1000.0 * output_rate
    )


def run_cloud_review_call(
    *,
    cfg: AssistantConfig,
    record: FileExecutionRecord,
    candidate: CloudCandidate,
    day,
    spent_so_far_usd: float,
    mode: str,
    manual_override: bool,
) -> tuple[CloudCandidate, float]:
    """Call LiteLLM once for a gated cloud-review candidate and persist output."""
    prompt = _build_cloud_review_prompt(record)
    estimated_prompt_tokens = _estimate_tokens(prompt)
    preflight_cost = estimate_cloud_cost_usd(
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=0,
        pricing=cfg.cloud_model_pricing,
    )
    if spent_so_far_usd + preflight_cost > cfg.daily_cloud_budget_usd:
        candidate.gate_passed = False
        candidate.gate_block_reason = "budget exceeded"
        candidate.escalated = False
        candidate.estimated_cost_usd = None
        return candidate, spent_so_far_usd

    response = litellm_client.chat_completion(
        [{"role": "user", "content": prompt}],
        model_group=CLOUD_MODEL_GROUP,
        base_url=cfg.litellm_base_url,
        mode=mode,
        manual_override=manual_override,
    )
    completion_tokens = _estimate_tokens(response)
    actual_cost = estimate_cloud_cost_usd(
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=completion_tokens,
        pricing=cfg.cloud_model_pricing,
    )
    if spent_so_far_usd + actual_cost > cfg.daily_cloud_budget_usd:
        candidate.gate_passed = False
        candidate.gate_block_reason = "budget exceeded"
        candidate.escalated = False
        candidate.estimated_cost_usd = None
        return candidate, spent_so_far_usd

    response_path = _write_cloud_response(cfg, day, record.file_path, response)
    candidate.escalated = True
    candidate.cloud_response_chars = len(response)
    candidate.estimated_cost_usd = actual_cost
    candidate.cloud_response_path = str(response_path)
    record.escalated_to_cloud = True
    record.cloud_response_chars = len(response)
    return candidate, spent_so_far_usd + actual_cost


def _build_cloud_review_prompt(record: FileExecutionRecord) -> str:
    return "\n".join(
        [
            "Review this file after local extraction failed quality gates.",
            "Return concise findings, risks, and actionable next steps.",
            "Do not modify files or perform external actions.",
            "",
            f"File: {record.file_path}",
            f"Primary model group: {record.primary_model_group}",
            f"Secondary model group: {record.secondary_model_group or '(none)'}",
            f"Local error: {record.error or '(none)'}",
        ]
    )


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _write_cloud_response(
    cfg: AssistantConfig,
    day,
    file_path: str,
    response: str,
) -> Path:
    cloud_dir = dated_output_dir(cfg, day=day) / "_cloud"
    cloud_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file_path).name.replace("/", "_").replace(":", "_")
    target = cloud_dir / f"{safe_name}.md"
    target.write_text(response.strip() + "\n", encoding="utf-8")
    return target
