from __future__ import annotations

from assistant_core.schemas import ClarificationQuestion, ReadinessScore, WorkPacket


QUESTION_BANK = {
    "objective": ("objective", "What exact outcome should this work produce, and what should be considered out of scope?", 100, True),
    "output_format": ("outputs", "What exact output files or formats do you want at the end?", 95, True),
    "sources": ("sources", "Which folders or files are in scope, and are any sources explicitly off-limits?", 90, True),
    "privacy_cloud_policy": ("privacy/cloud", "Is cloud fallback explicitly allowed for this packet, or must it stay fully local?", 88, True),
    "quality_threshold": ("quality", "What quality bar should I optimize for: speed, completeness, factuality, criticality, or polish?", 70, False),
    "audience": ("audience", "Who is the output for: only you, a direct report, executive team, CEO, board, or someone else?", 65, False),
    "assumption_policy": ("assumptions", "Should action owners, deadlines, and priorities be inferred when likely, or only used when explicit?", 60, False),
    "escalation_policy": ("escalation", "When should this stop and ask for human review instead of continuing?", 55, False),
    "success_criteria": ("stop conditions", "What makes the work successful enough to stop?", 50, False),
}


def generate_questions(
    packet: WorkPacket,
    readiness: ReadinessScore,
    *,
    round_number: int = 1,
    max_questions: int = 7,
) -> list[ClarificationQuestion]:
    missing = readiness.blocking_gaps + readiness.non_blocking_gaps
    ranked = sorted((QUESTION_BANK[name] for name in missing if name in QUESTION_BANK), key=lambda item: item[2], reverse=True)
    questions = ranked[:max_questions]
    return [
        ClarificationQuestion(
            work_packet_id=packet.id,
            round_number=round_number,
            category=category,
            question=question,
            priority=priority,
            blocking=blocking,
        )
        for category, question, priority, blocking in questions
    ]
