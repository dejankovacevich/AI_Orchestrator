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


def deterministic_completeness_evaluator(
    output_text: str,
    required_terms: list[str] | None = None,
    *,
    required_citation_count: int = 0,
) -> EvaluationResult:
    """Fast, model-free check that the output has the right shape.

    Two checks:
      - ``required_terms`` — every term must appear (case-insensitive)
        somewhere in the output. Missing terms are reported.
      - ``required_citation_count`` — when > 0, the output must contain at
        least that many ``Source:`` markers. Used for grounding enforcement
        when ``WorkPacket.grounding_required`` is True.

    Returns a populated EvaluationResult. ``pass`` is False if either check
    fails or the output is empty.
    """
    terms = required_terms or []
    text_lower = output_text.lower()
    missing_terms = [term for term in terms if term.lower() not in text_lower]
    citation_count = text_lower.count("source:")
    citations_short = max(0, required_citation_count - citation_count)

    has_content = bool(output_text.strip())
    passed = (not missing_terms) and (citations_short == 0) and has_content

    missing_info: list[str] = list(missing_terms)
    if citations_short > 0:
        missing_info.append(
            f"need {required_citation_count} 'Source:' citations, got {citation_count}"
        )

    score = 0.8 if passed else 0.5
    grounding_score = (
        score if required_citation_count == 0
        else (1.0 if citations_short == 0 else 0.4)
    )

    return EvaluationResult.model_validate(
        {
            "pass": passed,
            "quality_score": score,
            "grounding_score": grounding_score,
            "completeness_score": score,
            "actionability_score": score,
            "contradiction_score": 0.0,
            "hallucination_risk": "low" if passed else "medium",
            "missing_information": missing_info,
            "needs_retry": not passed,
            "recommended_next_step": "pass" if passed else "retry_local_secondary",
            "reason": (
                "Deterministic fallback evaluation."
                + (" Grounding enforced." if required_citation_count else "")
            ),
        }
    )
