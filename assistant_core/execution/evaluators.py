from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from assistant_core.schemas import EvaluationResult


INVALID_EVALUATION = EvaluationResult.model_validate(
    {
        "pass": False,
        "quality_score": 0.0,
        "grounding_score": 0.0,
        "completeness_score": 0.0,
        "actionability_score": 0.0,
        "contradiction_score": 1.0,
        "hallucination_risk": "high",
        "missing_information": ["Evaluator did not return valid strict JSON."],
        "needs_retry": True,
        "recommended_next_step": "retry_local_secondary",
        "reason": "Invalid evaluator JSON.",
    }
)


def parse_evaluator_json(raw: str) -> EvaluationResult:
    try:
        payload: dict[str, Any] = json.loads(raw)
        return EvaluationResult.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return INVALID_EVALUATION


def deterministic_completeness_evaluator(output_text: str, required_terms: list[str] | None = None) -> EvaluationResult:
    terms = required_terms or []
    missing = [term for term in terms if term.lower() not in output_text.lower()]
    passed = not missing and bool(output_text.strip())
    score = 0.8 if passed else 0.5
    return EvaluationResult.model_validate(
        {
            "pass": passed,
            "quality_score": score,
            "grounding_score": score,
            "completeness_score": score,
            "actionability_score": score,
            "contradiction_score": 0.0,
            "hallucination_risk": "low" if passed else "medium",
            "missing_information": missing,
            "needs_retry": not passed,
            "recommended_next_step": "pass" if passed else "retry_local_secondary",
            "reason": "Deterministic fallback evaluation.",
        }
    )
