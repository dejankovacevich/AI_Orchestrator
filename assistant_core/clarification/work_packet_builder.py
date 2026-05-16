from __future__ import annotations

import re

from assistant_core.schemas import ExecutionPlan, WorkPacket


STANDARD_OUTPUTS = [
    "00_STATUS.json",
    "01_MORNING_BRIEF.md",
    "02_TODAY_PRIORITIES.md",
    "03_ACTIONS_BY_PERSON.md",
    "04_DECISIONS_NEEDED.md",
    "05_RISKS_AND_BLOCKERS.md",
    "06_DRAFT_MESSAGES.md",
    "07_MEETING_PREP.md",
    "08_CLOUD_REVIEW_CANDIDATES.md",
    "09_AUDIT_LOG.md",
]


def build_initial_work_packet(title: str, description: str) -> WorkPacket:
    lower = f"{title}\n{description}".lower()
    desired_outputs: list[str] = []
    if "morning" in lower or "tomorrow" in lower or "brief" in lower:
        desired_outputs = ["01_MORNING_BRIEF.md", "02_TODAY_PRIORITIES.md", "05_RISKS_AND_BLOCKERS.md"]

    high_stakes = any(term in lower for term in ["board", "ceo", "legal", "investor", "high-stakes", "high stakes"])
    return WorkPacket(
        title=title,
        objective=description.strip() or None,
        raw_user_request=description,
        high_stakes=high_stakes,
        desired_outputs=desired_outputs,
        execution_plan=ExecutionPlan(
            summary="Clarify the task, confirm source and output boundaries, then prepare for overnight execution only when ready.",
            steps=[
                "Confirm objective, outputs, sources, privacy policy, and success criteria.",
                "Score readiness using deterministic dimensions.",
                "Only execute in NIGHT_MODE or explicit manual resume after threshold is met.",
            ],
            risks=[
                "Source scope may be ambiguous.",
                "Output quality bar may be unstated.",
                "Cloud fallback is disabled unless explicitly authorized.",
            ],
            stop_conditions=[
                "Cloud policy unclear.",
                "Sources unclear.",
                "Output format unclear.",
            ],
        ),
    )


def update_packet_from_answers(packet: WorkPacket, answers_text: str) -> WorkPacket:
    text = answers_text.strip()
    lower = text.lower()
    updates = packet.model_copy(deep=True)
    if "cloud" in lower:
        disallowed = any(term in lower for term in ["do not use cloud", "no cloud", "cloud: no", "cloud disabled", "must stay local"])
        allowed = (
            any(term in lower for term in ["cloud allowed", "allow cloud", "claude allowed", "cloud fallback allowed"])
            and not disallowed
        )
        updates.cloud_policy = {"allowed": allowed, "explicit": True}

    source_paths = _extract_localai_paths(text)
    if source_paths:
        updates.source_paths = source_paths
        updates.source_policy = updates.source_policy or {"scope": "see supplied answers"}
    elif "source" in lower or "folder" in lower or "file" in lower:
        updates.source_policy = updates.source_policy or {"scope": "see supplied answers"}

    if "output" in lower or ".md" in lower or "brief" in lower:
        outputs = _infer_outputs(lower)
        if outputs:
            updates.desired_outputs = sorted(set(updates.desired_outputs + outputs))
        updates.output_policy = updates.output_policy or {"format": "see supplied answers"}

    audience = _extract_line_value(text, "audience")
    if audience:
        updates.audience = audience
    elif "for me" in lower or "private" in lower:
        updates.audience = updates.audience or "private user"

    if "quality" in lower or "optimize" in lower:
        updates.quality_threshold = _extract_line_value(text, "quality") or updates.quality_threshold or "see supplied answers"
    if "infer" in lower or "assumption" in lower:
        updates.assumption_policy = _extract_line_value(text, "assumptions") or updates.assumption_policy or "see supplied answers"
    if "stop" in lower or "human review" in lower or "ask" in lower:
        updates.escalation_policy = _extract_line_value(text, "stop conditions") or updates.escalation_policy or "see supplied answers"
    if "success" in lower or "done" in lower:
        success = _extract_line_value(text, "success")
        updates.success_criteria = updates.success_criteria or ([success] if success else ["see supplied answers"])
    return updates


def _extract_localai_paths(text: str) -> list[str]:
    paths: list[str] = []
    for match in re.findall(r"~/LocalAI/[A-Za-z0-9_./-]+", text):
        cleaned = match.rstrip(".,;:")
        if cleaned not in paths:
            paths.append(cleaned)
    return paths


def _extract_line_value(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^\s*-?\s*{re.escape(label)}\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip().rstrip(" .") if match else None


def _infer_outputs(lower_text: str) -> list[str]:
    outputs: list[str] = []
    if "morning brief" in lower_text or "brief" in lower_text:
        outputs.append("01_MORNING_BRIEF.md")
    if "priorit" in lower_text:
        outputs.append("02_TODAY_PRIORITIES.md")
    if "risk" in lower_text or "blocker" in lower_text:
        outputs.append("05_RISKS_AND_BLOCKERS.md")
    if "meeting prep" in lower_text:
        outputs.append("07_MEETING_PREP.md")
    return outputs
