from assistant_core.clarification.readiness import score_readiness
from assistant_core.schemas import WorkPacket


def test_readiness_below_threshold_when_core_context_is_unclear():
    packet = WorkPacket(
        title="Prepare me for tomorrow",
        objective="Prepare me for tomorrow from my notes.",
        raw_user_request="Prepare me for tomorrow from my notes.",
    )

    result = score_readiness(packet)

    assert result.status == "UNDERDEFINED"
    assert result.score < 0.65
    assert "output_format" in result.dimension_scores
    assert result.blocking_gaps


def test_ready_for_overnight_when_blocking_dimensions_are_filled():
    packet = WorkPacket(
        title="Morning prep",
        objective="Prepare a private morning brief from selected notes.",
        raw_user_request="Prepare me for tomorrow from my notes.",
        desired_outputs=[
            "01_MORNING_BRIEF.md",
            "02_TODAY_PRIORITIES.md",
            "05_RISKS_AND_BLOCKERS.md",
        ],
        source_paths=["~/LocalAI/inbox/notes"],
        audience="private user",
        assumption_policy="infer low-risk priorities, label all assumptions",
        escalation_policy="human review for unclear ownership or missing source evidence",
        success_criteria=["clear priorities", "risks identified", "sources respected"],
        cloud_policy={"allowed": False, "explicit": True},
        source_policy={"scope": "selected notes only"},
        output_policy={"format": "standard morning markdown packet"},
    )

    result = score_readiness(packet)

    assert result.status == "READY_FOR_OVERNIGHT"
    assert result.score >= 0.85


def test_high_stakes_requires_high_confidence_threshold():
    packet = WorkPacket(
        title="Board prep",
        objective="Prepare board-ready material from selected notes.",
        raw_user_request="Prepare board prep.",
        high_stakes=True,
        desired_outputs=["board_brief.md"],
        source_paths=["~/LocalAI/inbox/docs"],
        audience="board",
        quality_threshold="board-ready and sourced",
        assumption_policy="do not infer; flag gaps",
        escalation_policy="human review before use",
        success_criteria=["accurate", "complete"],
        cloud_policy={"allowed": False, "explicit": True},
        source_policy={"scope": "selected docs only"},
        output_policy={"format": "markdown brief"},
    )

    result = score_readiness(packet)

    assert result.score >= 0.85
    assert result.status == "READY_HIGH_CONFIDENCE"
