from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from assistant_core.config import AssistantConfig
from assistant_core.execution import runner as runner_module
from assistant_core.execution.runner import (
    PRIMARY_GROUP,
    run_execution_for_packet,
)
from assistant_core.schemas import ExecutionResult, WorkPacket


def _cfg_for_tmp(tmp_path: Path) -> AssistantConfig:
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


def _packet_with_source(source_path: Path, **overrides) -> WorkPacket:
    base = {
        "title": "Test packet",
        "objective": "Generate a test brief.",
        "raw_user_request": "Generate a test brief.",
        "audience": "private user",
        "quality_threshold": "factuality first",
        "assumption_policy": "infer with labels",
        "escalation_policy": "stop on missing sources",
        "success_criteria": ["produces a brief"],
        "desired_outputs": ["01_MORNING_BRIEF.md"],
        "source_paths": [str(source_path)],
        "cloud_policy": {"allowed": False, "explicit": True},
        "source_policy": {"scope": str(source_path)},
        "output_policy": {"format": "markdown"},
    }
    base.update(overrides)
    return WorkPacket.model_validate(base)


def _fake_backend(responses: list[str]):
    """Returns a backend callable that yields the given responses in order."""
    iterator = iter(responses)

    def _impl(model_group, prompt, mode, manual_override):
        return next(iterator)

    return _impl


@pytest.fixture
def inbox_with_one_note(tmp_path: Path) -> Path:
    inbox = tmp_path / "LocalAI" / "inbox" / "notes"
    inbox.mkdir(parents=True)
    note = inbox / "2026-W20-recap.md"
    note.write_text(
        "Met with Scope1 about Q3 staffing. Decision needed on hire vs reallocate.\n"
        "Risk: vendor X renewal deadline Friday.\n"
        "Priority: get back to legal before noon.\n",
        encoding="utf-8",
    )
    return inbox


def test_blocked_by_safety_in_strict_day_mode(tmp_path, inbox_with_one_note):
    cfg = _cfg_for_tmp(tmp_path)
    packet = _packet_with_source(inbox_with_one_note)
    backend = _fake_backend(["should not be called"])

    result = run_execution_for_packet(
        packet=packet,
        mode="DAY_MODE",
        manual_override=False,
        backend=backend,
        cfg=cfg,
        persist_to_db=False,
    )

    assert result.status == "BLOCKED_BY_SAFETY"
    assert any("Safety gate" in e for e in result.errors)
    assert result.files_processed == 0
    assert result.model_calls == 0


def test_blocked_status_short_circuits_before_loading_files(tmp_path):
    cfg = _cfg_for_tmp(tmp_path)
    # Path does not need to exist - we should never get there.
    packet = _packet_with_source(tmp_path / "does_not_exist")
    backend = _fake_backend([])

    result = run_execution_for_packet(
        packet=packet, mode="DAY_MODE", backend=backend, cfg=cfg, persist_to_db=False
    )
    assert result.status == "BLOCKED_BY_SAFETY"


def test_no_sources_when_path_empty(tmp_path):
    cfg = _cfg_for_tmp(tmp_path)
    empty_dir = tmp_path / "LocalAI" / "inbox" / "empty"
    empty_dir.mkdir(parents=True)
    packet = _packet_with_source(empty_dir)
    backend = _fake_backend([])

    result = run_execution_for_packet(
        packet=packet,
        mode="NIGHT_MODE",
        backend=backend,
        cfg=cfg,
        persist_to_db=False,
    )
    assert result.status == "NO_SOURCES"
    assert result.model_calls == 0


def test_end_to_end_with_single_source(tmp_path, inbox_with_one_note):
    cfg = _cfg_for_tmp(tmp_path)
    packet = _packet_with_source(inbox_with_one_note)

    extract_response = (
        "## Priorities\n- Get back to legal before noon.\n\n"
        "## Decisions needed\n- Hire vs reallocate for Q3 staffing.\n\n"
        "## Risks / Blockers\n- Vendor X renewal deadline Friday. Severity: high.\n\n"
        "## Action items (with owners where stated)\n- (none)\n\n"
        "## Draft messages (DO NOT SEND; for human review)\n- (none)\n\n"
        "## Open questions\n- Is the legal followup blocking the staffing decision?\n\n"
        "## Assumptions made\n- Assumption: \"vendor X\" refers to the renewal we discussed Monday.\n"
    )
    brief_response = (
        "# Morning Brief - 2026-05-17\n\n"
        "## Today's three things\n"
        "1. Reply to legal before noon (Source: 2026-W20-recap.md)\n"
        "2. Decide Q3 staffing hire vs reallocate (Source: 2026-W20-recap.md)\n"
        "3. Confirm vendor X renewal by Friday (Source: 2026-W20-recap.md)\n\n"
        "## Decisions needed\n- Q3 staffing hire vs reallocate\n\n"
        "## Risks surfaced\n- Vendor X renewal deadline (high)\n\n"
        "## Sources used\n- 2026-W20-recap.md\n\n"
        "## Confidence\nMedium - based on one source file.\n"
    )
    backend = _fake_backend([extract_response, brief_response])

    result = run_execution_for_packet(
        packet=packet,
        mode="NIGHT_MODE",
        backend=backend,
        cfg=cfg,
        day=date(2026, 5, 17),
        persist_to_db=False,
    )

    assert result.status == "COMPLETED", result.errors
    assert result.files_processed == 1
    assert result.files_failed == 0
    assert result.model_calls == 2  # one extract + one synth
    assert result.output_dir is not None
    output_dir = Path(result.output_dir)
    assert (output_dir / "01_MORNING_BRIEF.md").exists()
    assert (output_dir / "00_STATUS.json").exists()
    assert (output_dir / "09_AUDIT_LOG.md").exists()
    extracts = list((output_dir / "_extractions").glob("*.md"))
    assert len(extracts) == 1

    brief_text = (output_dir / "01_MORNING_BRIEF.md").read_text(encoding="utf-8")
    assert "Today's three things" in brief_text

    status_blob = json.loads((output_dir / "00_STATUS.json").read_text(encoding="utf-8"))
    assert status_blob["files_processed"] == 1


def test_failing_primary_model_marks_partial_failure(tmp_path, inbox_with_one_note):
    cfg = _cfg_for_tmp(tmp_path)
    packet = _packet_with_source(inbox_with_one_note)

    def raising_backend(model_group, prompt, mode, manual_override):
        raise RuntimeError("Ollama is sad")

    result = run_execution_for_packet(
        packet=packet,
        mode="NIGHT_MODE",
        backend=raising_backend,
        cfg=cfg,
        persist_to_db=False,
    )
    assert result.status == "PARTIAL_FAILURE"
    assert result.files_failed == 1
    assert result.files_processed == 0
    assert any("model failed" in (rec.error or "") for rec in result.file_records)


def test_synthesis_failure_falls_back_to_deterministic_concat(tmp_path, inbox_with_one_note):
    cfg = _cfg_for_tmp(tmp_path)
    packet = _packet_with_source(inbox_with_one_note)

    extract_response = "## Priorities\n- Reply to legal\n## Decisions needed\n- Q3 staffing\n## Risks / Blockers\n- Vendor X\n"

    call_count = {"n": 0}

    def half_broken_backend(model_group, prompt, mode, manual_override):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return extract_response
        raise RuntimeError("synthesis broke")

    result = run_execution_for_packet(
        packet=packet,
        mode="NIGHT_MODE",
        backend=half_broken_backend,
        cfg=cfg,
        persist_to_db=False,
    )

    assert result.status == "COMPLETED"  # extraction succeeded; fallback brief written
    assert result.files_processed == 1
    assert any("synthesis failed" in e for e in result.errors)
    brief = Path(result.output_dir) / "01_MORNING_BRIEF.md"
    text = brief.read_text(encoding="utf-8")
    assert "deterministic fallback" in text


def test_manual_override_lets_run_proceed_in_day_mode(tmp_path, inbox_with_one_note):
    cfg = _cfg_for_tmp(tmp_path)
    packet = _packet_with_source(inbox_with_one_note)
    backend = _fake_backend(["## Priorities\n- one\n## Decisions needed\n- d\n## Risks / Blockers\n- r\n", "# Morning Brief - x\n"])

    result = run_execution_for_packet(
        packet=packet,
        mode="DAY_MODE",
        manual_override=True,
        backend=backend,
        cfg=cfg,
        persist_to_db=False,
    )
    assert result.status == "COMPLETED"


def test_default_backend_calls_ollama_admin_quick_prompt(tmp_path, inbox_with_one_note):
    """Smoke test the default backend wiring (no actual HTTP)."""
    with patch.object(
        runner_module.ollama_admin,
        "tag_to_group_mapping",
        return_value={"qwen3:30b-a3b": PRIMARY_GROUP},
    ), patch.object(
        runner_module.ollama_admin,
        "quick_prompt",
        return_value="fake-response",
    ) as fake_quick:
        out = runner_module._default_backend(
            PRIMARY_GROUP, "hello", "NIGHT_MODE", False
        )
    assert out == "fake-response"
    args, kwargs = fake_quick.call_args
    assert args[0] == "qwen3:30b-a3b"
    assert kwargs.get("mode") == "NIGHT_MODE"


def test_default_backend_errors_on_unmapped_group():
    with patch.object(
        runner_module.ollama_admin, "tag_to_group_mapping", return_value={}
    ):
        with pytest.raises(ValueError, match="No Ollama tag"):
            runner_module._default_backend(PRIMARY_GROUP, "x", "NIGHT_MODE", False)
