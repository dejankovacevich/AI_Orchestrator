"""Task-type machinery: auto-detection, prompt selection, output routing.

Covers the work_packet_builder classifier, the prompt template registry,
the output filename map in steps.py, and grounding/citation enforcement
in the deterministic evaluator. These features are what makes the system
useful to both the indie-hacker persona (code_review) and the researcher
persona (grounding_required).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from assistant_core.clarification.work_packet_builder import (
    build_initial_work_packet,
    detect_task_type,
)
from assistant_core.execution import steps
from assistant_core.execution.evaluators import (
    deterministic_completeness_evaluator,
)
from assistant_core.execution.prompts import (
    CODE_REVIEW_EXTRACT_TEMPLATE,
    EXTRACT_TEMPLATES,
    MORNING_BRIEF_EXTRACT_TEMPLATE,
    SYNTHESIZE_TEMPLATES,
    TEST_GENERATION_EXTRACT_TEMPLATE,
    format_extract_prompt,
    format_synthesize_prompt,
)
from assistant_core.schemas import ExecutionResult, WorkPacket
from assistant_core.execution.context import StepContext
from assistant_core.config import AssistantConfig


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _cfg(tmp_path: Path) -> AssistantConfig:
    base = {
        "local_ai_root": tmp_path / "LocalAI",
        "inbox_dir": tmp_path / "LocalAI/inbox",
        "output_dir": tmp_path / "LocalAI/output",
        "archive_dir": tmp_path / "LocalAI/archive",
        "log_dir": tmp_path / "LocalAI/logs",
        "work_packets_dir": tmp_path / "LocalAI/work_packets",
        "obsidian_vault_dir": tmp_path / "Obsidian/LocalAI-ChiefOfStaff",
        "ollama_base_url": "http://localhost:11434",
        "litellm_base_url": "http://localhost:4000",
        "temporal_address": "localhost:7233",
        "postgres_url": "postgresql://localai:localai@localhost:5432/localai",
        "day_mode_start": "07:30",
        "night_mode_start": "01:30",
        "night_mode_end": "07:00",
    }
    return AssistantConfig.model_validate(base)


def _ctx(tmp_path, *, task_type="morning_brief", grounding_required=False) -> StepContext:
    packet = WorkPacket.model_validate(
        {
            "title": f"Test {task_type}",
            "objective": "exercise the pipeline",
            "task_type": task_type,
            "grounding_required": grounding_required,
            "raw_user_request": "test",
            "audience": "private user",
            "source_paths": [str(tmp_path)],
        }
    )
    return StepContext(
        packet=packet,
        cfg=_cfg(tmp_path),
        backend=lambda *_, **__: "fake",
        mode="NIGHT_MODE",
        manual_override=False,
        day=date(2026, 5, 21),
        persist_to_db=False,
        result=ExecutionResult(work_packet_id=packet.id, mode="NIGHT_MODE"),
    )


# ---------------------------------------------------------------------------
# detect_task_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Review this code for clarity", "code_review"),
        ("Suggest a refactor that improves testability", "code_review"),
        ("Generate tests for payments.py", "test_generation"),
        ("Write missing unit test cases", "test_generation"),
        ("Generate docstrings and a README section", "doc_generation"),
        ("Add documentation to this module", "doc_generation"),
        ("Extract decisions from this week's transcripts", "decision_capture"),
        ("List action items with owners", "decision_capture"),
        ("Surface risks and blockers from this week", "risk_scan"),
        ("Run a risk scan on the notes", "risk_scan"),
        ("Prepare me for tomorrow from my notes", "morning_brief"),
        ("", "morning_brief"),
    ],
)
def test_detect_task_type_classifies_known_intents(text, expected):
    assert detect_task_type(text) == expected


def test_build_initial_work_packet_auto_detects_code_review():
    p = build_initial_work_packet(
        "PR review", "Please review this code and propose a refactor."
    )
    assert p.task_type == "code_review"
    assert "01_CODE_REVIEW.md" in p.desired_outputs


def test_build_initial_work_packet_auto_detects_grounding_required():
    p = build_initial_work_packet(
        "Audit-grade summary",
        "Read these regulated notes and produce a summary where every claim must cite source.",
    )
    assert p.grounding_required is True


# ---------------------------------------------------------------------------
# Prompt template selection
# ---------------------------------------------------------------------------

def test_extract_prompt_uses_morning_brief_template_by_default(tmp_path):
    ctx = _ctx(tmp_path, task_type="morning_brief")
    prompt = format_extract_prompt(
        packet=ctx.packet, source_path="note.md", kind="md", content="hi"
    )
    assert "extracting structured signals" in prompt
    assert "Today's three things" not in prompt  # that lives in synthesize


def test_extract_prompt_uses_code_review_template_for_code_review_packet(tmp_path):
    ctx = _ctx(tmp_path, task_type="code_review")
    prompt = format_extract_prompt(
        packet=ctx.packet, source_path="x.py", kind="py", content="def foo(): ..."
    )
    assert "Refactor proposal" in prompt
    assert "Missing test cases" in prompt
    assert "Stay within the file's existing dependency set" in prompt


def test_extract_prompt_uses_test_generation_template_for_test_generation_packet(tmp_path):
    ctx = _ctx(tmp_path, task_type="test_generation")
    prompt = format_extract_prompt(
        packet=ctx.packet, source_path="payments.py", kind="py", content="def pay(): ..."
    )
    assert "Missing test cases" in prompt
    assert "Edge cases to cover" in prompt
    assert "Test scaffolding suggestions" in prompt
    assert "Stay within the file's existing dependency set" in prompt


def test_unknown_task_type_falls_back_to_morning_brief(tmp_path):
    # Bypass pydantic literal check by using model_construct
    ctx = _ctx(tmp_path)
    ctx.packet = WorkPacket.model_construct(
        **{**ctx.packet.model_dump(), "task_type": "not_yet_implemented"}
    )
    prompt = format_extract_prompt(
        packet=ctx.packet, source_path="a.md", kind="md", content="x"
    )
    # Morning brief template's signature line
    assert "extracting structured signals" in prompt


def test_synthesize_prompt_uses_code_review_template_for_code_review_packet(tmp_path):
    ctx = _ctx(tmp_path, task_type="code_review")
    prompt = format_synthesize_prompt(
        packet=ctx.packet, extractions="...", today="2026-05-21"
    )
    assert "Code Review" in prompt
    assert "Top recommended changes" in prompt


def test_template_registry_includes_required_keys():
    assert "morning_brief" in EXTRACT_TEMPLATES
    assert "code_review" in EXTRACT_TEMPLATES
    assert "test_generation" in EXTRACT_TEMPLATES
    assert "morning_brief" in SYNTHESIZE_TEMPLATES
    assert "code_review" in SYNTHESIZE_TEMPLATES
    assert "test_generation" in SYNTHESIZE_TEMPLATES


# ---------------------------------------------------------------------------
# Output filename routing
# ---------------------------------------------------------------------------

def test_write_outputs_writes_code_review_filename_for_code_review(tmp_path):
    ctx = _ctx(tmp_path, task_type="code_review")
    ctx.brief_md = "# Code Review\nfindings"
    ctx.extractions = [("x.py", "## Clarity issues\n- one\n")]
    steps.write_outputs(ctx)
    out = ctx.output_dir
    assert (out / "01_CODE_REVIEW.md").exists()
    assert not (out / "01_MORNING_BRIEF.md").exists()


def test_write_outputs_writes_morning_brief_filename_by_default(tmp_path):
    ctx = _ctx(tmp_path, task_type="morning_brief")
    ctx.brief_md = "# Morning Brief\n"
    ctx.extractions = [("note.md", "## Priorities\n- one\n")]
    steps.write_outputs(ctx)
    out = ctx.output_dir
    assert (out / "01_MORNING_BRIEF.md").exists()


def test_task_output_filenames_covers_every_known_task():
    expected_tasks = {
        "morning_brief",
        "code_review",
        "test_generation",
        "doc_generation",
        "decision_capture",
        "risk_scan",
    }
    assert set(steps.TASK_OUTPUT_FILENAMES) == expected_tasks


# ---------------------------------------------------------------------------
# Obsidian routing
# ---------------------------------------------------------------------------

def test_write_obsidian_routes_code_review_to_work_packets(tmp_path):
    ctx = _ctx(tmp_path, task_type="code_review")
    ctx.brief_md = "# Code Review\nbody"
    steps.write_obsidian(ctx)
    obsidian_path = Path(ctx.result.obsidian_brief_path)
    assert "02_Work_Packets" in obsidian_path.parts
    assert "code_review" in obsidian_path.name
    assert obsidian_path.exists()


def test_write_obsidian_routes_morning_brief_to_daily_briefs(tmp_path):
    ctx = _ctx(tmp_path, task_type="morning_brief")
    ctx.brief_md = "# Morning Brief\nbody"
    steps.write_obsidian(ctx)
    obsidian_path = Path(ctx.result.obsidian_brief_path)
    assert "01_Daily_Briefs" in obsidian_path.parts
    assert obsidian_path.exists()


# ---------------------------------------------------------------------------
# Grounding / citation enforcement in the evaluator
# ---------------------------------------------------------------------------

def test_deterministic_evaluator_passes_without_grounding_check():
    text = "## Priorities\n- a\n## Decisions needed\n- b\n## Risks\n- c\n"
    ev = deterministic_completeness_evaluator(
        text, ["priorities", "decisions", "risks"]
    )
    assert ev.pass_ is True


def test_deterministic_evaluator_requires_citations_when_count_set():
    text = (
        "## Priorities\n- a\n"
        "## Decisions needed\n- b\n"
        "## Risks\n- c\n"
    )
    ev = deterministic_completeness_evaluator(
        text,
        ["priorities", "decisions", "risks"],
        required_citation_count=3,
    )
    assert ev.pass_ is False
    assert any("citations" in info.lower() for info in ev.missing_information)


def test_deterministic_evaluator_passes_when_citations_are_present():
    text = (
        "## Priorities\n- a. Source: x\n"
        "## Decisions needed\n- b. Source: y\n"
        "## Risks\n- c. Source: z\n"
    )
    ev = deterministic_completeness_evaluator(
        text,
        ["priorities", "decisions", "risks"],
        required_citation_count=3,
    )
    assert ev.pass_ is True
    assert ev.grounding_score >= 0.9


def test_citation_floor_helper_only_active_when_grounding_required(tmp_path):
    ctx = _ctx(tmp_path, grounding_required=False)
    assert steps._citation_floor(ctx.packet) == 0
    ctx2 = _ctx(tmp_path, grounding_required=True)
    assert steps._citation_floor(ctx2.packet) >= 1


# ---------------------------------------------------------------------------
# End-to-end shape: grounding_required + bad output triggers retry
# ---------------------------------------------------------------------------

def test_grounding_required_failure_triggers_secondary_retry(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("content", encoding="utf-8")

    calls: list[str] = []

    def backend(group, prompt, mode_, override):
        calls.append(group)
        # Both attempts return text with required terms but no "Source:"
        return (
            "## Priorities\n- p\n"
            "## Decisions needed\n- d\n"
            "## Risks / Blockers\n- r\n"
        )

    ctx = _ctx(tmp_path, grounding_required=True)
    ctx.packet.source_paths = [str(inbox)]
    ctx.backend = backend
    steps.scan_sources(ctx)
    steps.process_sources(ctx)

    # Both attempts lack citations, so primary AND secondary both fail
    # the evaluator. Record should reflect retry attempted + cloud-review flag.
    assert calls == [steps.PRIMARY_GROUP, steps.SECONDARY_GROUP]
    rec = ctx.result.file_records[0]
    assert rec.retry_attempted is True
    assert rec.retry_succeeded is False
    assert rec.needs_cloud_review is True