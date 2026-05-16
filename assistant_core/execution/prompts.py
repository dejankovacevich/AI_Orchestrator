EXECUTION_SYSTEM_PROMPT = """You execute only READY local-first work packets.
Do not modify original user files. Do not perform external writes. Use cloud only after policy authorization."""

EVALUATOR_PROMPT = """Return strict JSON only with pass, quality_score, grounding_score, completeness_score,
actionability_score, contradiction_score, hallucination_risk, missing_information, needs_retry,
recommended_next_step, and reason."""
