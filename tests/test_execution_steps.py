"""Per-step unit tests.

These tests verify each function in execution/steps.py in isolation by
hand-constructing a StepContext, calling the step, and asserting on the
ctx mutations. The full end-to-end run is covered in
test_execution_runner.py.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from assistant_core.config import AssistantConfig
from assistant_core.execution import steps
from assistant_core.execution.context import StepContext
from assistant_core.execution.graph import (
    EXECUTION_GRAPH,
    describe_execution_scaffold,
    step_names,
)
from assistant_core.schemas import ExecutionResult, FileExecutionRecord, WorkPacket


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


def _packet(source_paths: list[str]) -> WorkPacket:
    return WorkPacket.model_validate(
        {
            "title": "Step test packet",
            "objective": "Test individual steps.",
            "raw_user_request": "Test individual steps.",
            "audience": "private user",
            "quality_threshold": "factuality first",
            "assumption_policy": "label inferences",
            "escalation_policy": "stop on missing sources",
            "success_criteria": ["each step produces expected mutation"],
            "desired_outputs": ["01_MORNING_BRIEF.md"],
            "source_paths": source_paths,
            "cloud_policy": {"allowed": False, "explicit": True},
            "source_policy": {"scope": "test"},
            "output_policy": {"format": "markdown"},
        }
    )


def _make_ctx(tmp_path: Path, *, source_paths, mode="NIGHT_MODE", backend=None) -> StepContext:
    packet = _packet([str(p) for p in source_paths])
    if backend is None:
        def backend(model_group, prompt, mode_, override):
            return "default fake response"
    return StepContext(
        packet=packet,
        cfg=_cfg(tmp_path),
        backend=backend,
        mode=mode,
        manual_override=False,
        day=date(2026, 5, 18),
        persist_to_db=False,
        result=ExecutionResult(work_packet_id=packet.id, mode=mode),
    )


# ---------------------------------------------------------------------------
# Graph integrity tests
# ---------------------------------------------------------------------------

def test_graph_lists_callables_in_known_order():
    names = step_names()
    # First three are always: safety_gate, initialize_run, scan_sources
    assert names[0] == "safety_gate"
    assert names[1] == "initialize_run"
    assert names[2] == "scan_sources"
    # Last is always finalize_run
    assert names[-1] == "finalize_run"


def test_every_step_in_graph_is_callable():
    for step in EXECUTION_GRAPH:
        assert callable(step), f"{step} is not callable"


def test_describe_execution_scaffold_shape():
    scaffold = describe_execution_scaffold()
    assert scaffold["status"] == "wired"
    assert isinstance(scaffold["graph"], list)
    assert isinstance(scaffold["documented_steps"], list)
    assert len(scaffold["graph"]) == len(EXECUTION_GRAPH)


# ---------------------------------------------------------------------------
# safety_gate
# ---------------------------------------------------------------------------

def test_safety_gate_blocks_in_strict_day_mode(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path], mode="DAY_MODE")
    out = steps.safety_gate(ctx)
    assert out.halt is True
    assert out.result.status == "BLOCKED_BY_SAFETY"
    assert any("Safety gate refused" in e for e in out.result.errors)


def test_safety_gate_allows_in_night_mode(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path], mode="NIGHT_MODE")
    out = steps.safety_gate(ctx)
    assert out.halt is False
    assert out.result.status != "BLOCKED_BY_SAFETY"


def test_safety_gate_allows_with_manual_override(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path], mode="DAY_MODE")
    ctx.manual_override = True
    out = steps.safety_gate(ctx)
    assert out.halt is False


# ---------------------------------------------------------------------------
# scan_sources
# ---------------------------------------------------------------------------

def test_scan_sources_collects_supported_files_only(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "a.md").write_text("hi", encoding="utf-8")
    (inbox / "b.txt").write_text("hi", encoding="utf-8")
    (inbox / "c.png").write_bytes(b"\x89PNG")  # unsupported
    (inbox / "d.log").write_text("INFO ok", encoding="utf-8")

    ctx = _make_ctx(tmp_path, source_paths=[inbox])
    steps.scan_sources(ctx)
    paths = [Path(p).name for p in ctx.source_files]
    assert sorted(paths) == ["a.md", "b.txt", "d.log"]
    assert ctx.halt is False


def test_scan_sources_halts_when_no_supported_files(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "image.png").write_bytes(b"\x89PNG")
    ctx = _make_ctx(tmp_path, source_paths=[empty])
    steps.scan_sources(ctx)
    assert ctx.halt is True
    assert ctx.result.status == "NO_SOURCES"


def test_scan_sources_handles_missing_path_gracefully(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path / "definitely_not_there"])
    steps.scan_sources(ctx)
    assert ctx.halt is True
    assert any("does not exist" in e for e in ctx.result.errors)


# ---------------------------------------------------------------------------
# process_sources
# ---------------------------------------------------------------------------

def test_process_sources_extracts_via_backend(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("a meaningful note", encoding="utf-8")

    def backend(group, prompt, mode_, override):
        return "## Priorities\n- something\n## Decisions needed\n- d\n## Risks / Blockers\n- r\n"

    ctx = _make_ctx(tmp_path, source_paths=[inbox], backend=backend)
    steps.scan_sources(ctx)
    steps.process_sources(ctx)
    assert ctx.result.files_processed == 1
    assert ctx.result.files_failed == 0
    assert len(ctx.extractions) == 1
    assert ctx.extractions[0][1].startswith("## Priorities")
    assert ctx.result.model_calls == 1


def test_process_sources_failed_backend_marks_partial_failure(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("content", encoding="utf-8")

    def boom(group, prompt, mode_, override):
        raise RuntimeError("ollama unhappy")

    ctx = _make_ctx(tmp_path, source_paths=[inbox], backend=boom)
    steps.scan_sources(ctx)
    steps.process_sources(ctx)
    assert ctx.halt is True
    assert ctx.result.status == "PARTIAL_FAILURE"
    assert ctx.result.files_failed == 1


# ---------------------------------------------------------------------------
# synthesize_brief
# ---------------------------------------------------------------------------

def test_synthesize_brief_calls_backend_with_synthesis_prompt(tmp_path):
    seen = {"prompts": []}

    def backend(group, prompt, mode_, override):
        seen["prompts"].append(prompt)
        return "# Morning Brief - 2026-05-18\n\nbody.\n"

    ctx = _make_ctx(tmp_path, source_paths=[tmp_path], backend=backend)
    ctx.extractions = [("note.md", "## Priorities\n- one\n")]
    steps.synthesize_brief(ctx)
    assert ctx.brief_md.startswith("# Morning Brief")
    assert "## Priorities" in seen["prompts"][0]  # extraction was fed in
    assert ctx.result.model_calls == 1


def test_synthesize_brief_falls_back_when_backend_fails(tmp_path):
    def boom(group, prompt, mode_, override):
        raise RuntimeError("nope")

    ctx = _make_ctx(tmp_path, source_paths=[tmp_path], backend=boom)
    ctx.extractions = [("note.md", "## Priorities\n- one\n")]
    steps.synthesize_brief(ctx)
    assert "deterministic fallback" in ctx.brief_md
    assert any("synthesis failed" in e for e in ctx.result.errors)


# ---------------------------------------------------------------------------
# write_outputs
# ---------------------------------------------------------------------------

def test_write_outputs_creates_expected_files(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path])
    ctx.brief_md = "# Morning Brief\nbody"
    ctx.extractions = [("note.md", "## Priorities\n- one\n")]
    ctx.result.files_processed = 1
    ctx.result.files_failed = 0
    ctx.result.model_calls = 2
    steps.write_outputs(ctx)

    out = ctx.output_dir
    assert (out / "00_STATUS.json").exists()
    assert (out / "01_MORNING_BRIEF.md").exists()
    assert (out / "09_AUDIT_LOG.md").exists()
    assert len(list((out / "_extractions").glob("*.md"))) == 1
    # Artifact count: 1 status + 1 brief + 1 audit + 1 extraction
    assert ctx.result.artifacts_written == 4


# ---------------------------------------------------------------------------
# finalize_run
# ---------------------------------------------------------------------------

def test_finalize_run_sets_completed_when_no_failures(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path])
    ctx.result.files_processed = 2
    ctx.result.files_failed = 0
    steps.finalize_run(ctx)
    assert ctx.result.status == "COMPLETED"
    assert ctx.result.completed_at is not None


def test_finalize_run_sets_partial_failure_when_any_file_failed(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path])
    ctx.result.files_processed = 1
    ctx.result.files_failed = 1
    steps.finalize_run(ctx)
    assert ctx.result.status == "PARTIAL_FAILURE"


# ---------------------------------------------------------------------------
# Scaffolded steps are no-ops today
# ---------------------------------------------------------------------------

def test_cloud_review_gate_is_a_noop(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path])
    before = ctx.result.model_dump()
    steps.cloud_review_gate(ctx)
    assert ctx.result.model_dump() == before


def test_archive_processed_files_is_a_noop(tmp_path):
    ctx = _make_ctx(tmp_path, source_paths=[tmp_path])
    before = ctx.result.model_dump()
    steps.archive_processed_files(ctx)
    assert ctx.result.model_dump() == before
