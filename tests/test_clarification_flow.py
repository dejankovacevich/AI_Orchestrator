from assistant_core.clarification.graph import run_deterministic_clarification
from assistant_core.clarification.readiness import score_readiness
from assistant_core.clarification.work_packet_builder import build_initial_work_packet, update_packet_from_answers


def test_vague_task_asks_privacy_cloud_question():
    result = run_deterministic_clarification("Tomorrow prep", "Prepare me for tomorrow from my notes.")

    categories = {question.category for question in result.questions}

    assert "privacy/cloud" in categories
    assert result.readiness.status == "UNDERDEFINED"


def test_answers_fill_packet_without_allowing_cloud():
    packet = build_initial_work_packet("Morning prep", "Prepare me for tomorrow from my notes.")
    answers = """
    Outputs: morning brief, today priorities, risks/blockers, and meeting prep.
    Sources: only ~/LocalAI/inbox/notes and ~/LocalAI/inbox/docs.
    Cloud: do not use cloud fallback.
    Audience: private user only.
    Assumptions: infer low-risk priorities but label every assumption.
    Quality: optimize for factuality, criticality, and actionability.
    Stop conditions: stop for missing sources, unclear ownership, or anything requiring external action.
    Success: I can read it in the morning and know what matters first.
    """

    updated = update_packet_from_answers(packet, answers)
    readiness = score_readiness(updated)

    assert updated.cloud_policy == {"allowed": False, "explicit": True}
    assert updated.source_paths == ["~/LocalAI/inbox/notes", "~/LocalAI/inbox/docs"]
    assert "01_MORNING_BRIEF.md" in updated.desired_outputs
    assert updated.audience == "private user only"
    assert readiness.score >= 0.85
    assert readiness.blocking_gaps == []
