from __future__ import annotations

from assistant_core.schemas import ReadinessScore, WorkPacket


READINESS_WEIGHTS = {
    "objective": 0.18,
    "output_format": 0.14,
    "sources": 0.14,
    "privacy_cloud_policy": 0.14,
    "quality_threshold": 0.12,
    "audience": 0.10,
    "assumption_policy": 0.08,
    "escalation_policy": 0.06,
    "success_criteria": 0.04,
}


def _present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _dimension_scores(packet: WorkPacket) -> tuple[dict[str, float], dict[str, str]]:
    cloud_known = "allowed" in packet.cloud_policy or "allow_cloud" in packet.cloud_policy
    source_known = _present(packet.source_paths) or _present(packet.source_policy)
    output_known = _present(packet.desired_outputs) or _present(packet.output_policy)
    checks = {
        "objective": (_present(packet.objective), "Objective is explicit." if _present(packet.objective) else "Objective is missing or vague."),
        "output_format": (output_known, "Outputs are specified." if output_known else "Output format is unclear."),
        "sources": (source_known, "Source scope is specified." if source_known else "Source files or folders are unclear."),
        "privacy_cloud_policy": (cloud_known, "Cloud policy is explicit." if cloud_known else "Cloud policy is unclear."),
        "quality_threshold": (_present(packet.quality_threshold), "Quality threshold is specified." if _present(packet.quality_threshold) else "Quality bar is unclear."),
        "audience": (_present(packet.audience), "Audience is specified." if _present(packet.audience) else "Audience is unclear."),
        "assumption_policy": (_present(packet.assumption_policy), "Assumption policy is specified." if _present(packet.assumption_policy) else "Assumption policy is unclear."),
        "escalation_policy": (_present(packet.escalation_policy), "Escalation policy is specified." if _present(packet.escalation_policy) else "Escalation policy is unclear."),
        "success_criteria": (_present(packet.success_criteria), "Success criteria are specified." if _present(packet.success_criteria) else "Success criteria are missing."),
    }
    scores = {name: 1.0 if ok else 0.0 for name, (ok, _) in checks.items()}
    reasons = {name: reason for name, (_, reason) in checks.items()}
    return scores, reasons


def readiness_status(score: float, *, high_stakes: bool = False) -> str:
    if high_stakes:
        return "READY_HIGH_CONFIDENCE" if score >= 0.90 else "NEEDS_CLARIFICATION"
    if score >= 0.90:
        return "READY_HIGH_CONFIDENCE"
    if score >= 0.85:
        return "READY_FOR_OVERNIGHT"
    if score >= 0.65:
        return "NEEDS_CLARIFICATION"
    return "UNDERDEFINED"


def score_readiness(packet: WorkPacket) -> ReadinessScore:
    scores, reasons = _dimension_scores(packet)
    score = round(sum(scores[name] * READINESS_WEIGHTS[name] for name in READINESS_WEIGHTS), 4)
    blocking_names = {"objective", "output_format", "sources", "privacy_cloud_policy"}
    blocking_gaps = [name for name, value in scores.items() if value < 1.0 and name in blocking_names]
    non_blocking_gaps = [name for name, value in scores.items() if value < 1.0 and name not in blocking_names]
    return ReadinessScore(
        score=score,
        status=readiness_status(score, high_stakes=packet.high_stakes),
        dimension_scores=scores,
        reasons=reasons,
        blocking_gaps=blocking_gaps,
        non_blocking_gaps=non_blocking_gaps,
    )
