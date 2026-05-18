"""End-to-end execution runner for a single work packet.

This is the first real (non-stub) implementation of the overnight pipeline.
It is a minimal-but-working slice of the 18-step execution graph:

    load_packet -> scan_sources -> per_source(extract via local-main,
    evaluate) -> synthesize_brief via local-main -> write_outputs ->
    log_to_postgres -> generate_memory_candidates -> write_obsidian ->
    update_packet_status

Steps NOT yet wired (deliberate v1 scope):
    classify_file_task (everything routed to local-main)
    privacy_gate beyond the existing path checks
    execute_secondary_local_if_needed retry chain (placeholder hook only)
    reasoning_check via local-reasoner
    cloud_review_gate -> claude (still scaffolded)
    archive_processed_files

Designed to work with or without a Postgres connection: when storage is
unavailable, the runner still produces filesystem outputs and returns an
ExecutionResult with execution_run_id=None.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

from assistant_core.config import AssistantConfig, load_assistant_config
from assistant_core.execution.evaluators import (
    deterministic_completeness_evaluator,
)
from assistant_core.execution.file_utils import (
    UnsupportedFileType,
    chunk_text,
    load_supported_file,
)
from assistant_core.execution.output_writer import dated_output_dir, write_status
from assistant_core.execution.prompts import (
    format_extract_prompt,
    format_synthesize_prompt,
)
from assistant_core.llm import ollama_admin
from assistant_core.memory.memory_extractor import extract_memory_candidates
from assistant_core.memory.obsidian import write_daily_brief, write_memory_candidate
from assistant_core.paths import assert_within_roots, resolve_user_path
from assistant_core.safety import (
    SafetyError,
    assert_heavy_execution_allowed,
)
from assistant_core.schemas import (
    Artifact,
    ExecutionResult,
    FileExecutionRecord,
    MemoryCandidate,
    ModelCallLog,
    WorkPacket,
)


logger = logging.getLogger(__name__)


# Type alias: a callable that takes (model_group, prompt, mode, manual_override)
# and returns the model's text response. Lets tests inject a fake backend.
LLMBackend = Callable[[str, str, str, bool], str]


# ---------------------------------------------------------------------------
# Defaults and helpers
# ---------------------------------------------------------------------------

PRIMARY_GROUP = "local-main"
SECONDARY_GROUP = "local-secondary"
EVAL_REQUIRED_TERMS = ["priorities", "decisions", "risks"]


def _default_backend(
    model_group: str, prompt: str, mode: str, manual_override: bool
) -> str:
    """Call Ollama via the gate-checked admin layer.

    Resolves the group to a tag, then calls quick_prompt. This keeps a single
    place where every model call passes through assert_model_group_allowed.
    """
    mapping = ollama_admin.tag_to_group_mapping()
    reverse = {group: tag for tag, group in mapping.items()}
    tag = reverse.get(model_group)
    if tag is None:
        raise ValueError(f"No Ollama tag configured for group: {model_group}")
    return ollama_admin.quick_prompt(
        tag, prompt, mode=mode, manual_override=manual_override
    )


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def run_execution_for_packet(
    work_packet_id: str | None = None,
    *,
    packet: WorkPacket | None = None,
    mode: str = "DAY_MODE",
    manual_override: bool = False,
    backend: LLMBackend | None = None,
    cfg: AssistantConfig | None = None,
    day: date | None = None,
    persist_to_db: bool = True,
) -> ExecutionResult:
    """Run the overnight execution for one work packet.

    Provide either ``work_packet_id`` (will load from Postgres) or ``packet``
    (in-memory; useful for tests or direct CLI use).

    Safety gate is always checked first; ``mode`` must permit local model
    execution, either by being NIGHT_MODE / MANUAL_RESUME, or by having
    ``manual_override=True``, or by an active day-unlock flag.
    """
    cfg = cfg or load_assistant_config()
    backend = backend or _default_backend
    target_day = day or date.today()

    if packet is None:
        if work_packet_id is None:
            raise ValueError("Either packet or work_packet_id must be provided")
        packet = _load_packet_or_raise(work_packet_id)

    result = ExecutionResult(
        work_packet_id=packet.id,
        mode=mode,
    )

    # --- Gate -------------------------------------------------------
    try:
        assert_heavy_execution_allowed(mode, manual_override=manual_override)
    except SafetyError as exc:
        result.status = "BLOCKED_BY_SAFETY"
        result.errors.append(f"Safety gate refused execution: {exc}")
        result.completed_at = datetime.now(UTC)
        return result

    # --- Create execution_run row in Postgres (optional) ------------
    run_id_str: str | None = None
    if persist_to_db:
        run_id_str = _maybe_create_execution_run(
            work_packet_id=str(packet.id), mode=mode, errors=result.errors
        )
        if run_id_str:
            from uuid import UUID

            result.execution_run_id = UUID(run_id_str)

    # --- Scan sources -----------------------------------------------
    source_files = _scan_sources(packet, errors=result.errors)
    if not source_files:
        result.status = "NO_SOURCES"
        result.errors.append(
            "No supported source files found under packet.source_paths"
        )
        result.completed_at = datetime.now(UTC)
        _maybe_complete_execution_run(run_id_str, status="FAILED", errors=result.errors)
        return result

    # --- Per-source extraction --------------------------------------
    extractions: list[tuple[str, str]] = []  # (file_path, extraction_markdown)
    for source_path in source_files:
        record, extraction_text = _process_one_source(
            source_path=source_path,
            packet=packet,
            mode=mode,
            manual_override=manual_override,
            backend=backend,
            cfg=cfg,
            run_id_str=run_id_str,
            result=result,
            persist_to_db=persist_to_db,
        )
        result.file_records.append(record)
        if record.error is None and extraction_text is not None:
            extractions.append((source_path, extraction_text))
            result.files_processed += 1
        else:
            result.files_failed += 1

    # If literally nothing succeeded, finish here.
    if not extractions:
        result.status = "PARTIAL_FAILURE"
        result.completed_at = datetime.now(UTC)
        _maybe_complete_execution_run(
            run_id_str, status="FAILED", errors=result.errors
        )
        return result

    # --- Synthesize brief -------------------------------------------
    brief_md = _synthesize_brief(
        packet=packet,
        extractions=extractions,
        today=target_day.isoformat(),
        mode=mode,
        manual_override=manual_override,
        backend=backend,
        run_id_str=run_id_str,
        result=result,
        persist_to_db=persist_to_db,
    )

    # --- Write outputs ----------------------------------------------
    output_dir = dated_output_dir(cfg, day=target_day)
    result.output_dir = str(output_dir)
    _write_outputs(
        output_dir=output_dir,
        packet=packet,
        brief_md=brief_md,
        extractions=extractions,
        run_id_str=run_id_str,
        result=result,
        persist_to_db=persist_to_db,
    )

    # --- Obsidian copy ----------------------------------------------
    try:
        obsidian_path = write_daily_brief(brief_md, cfg=None, day=target_day)
        result.obsidian_brief_path = str(obsidian_path)
    except Exception as exc:  # pragma: no cover - obsidian path issues
        result.errors.append(f"Obsidian write failed: {exc}")

    # --- Memory candidates ------------------------------------------
    candidates = extract_memory_candidates(brief_md, source_path="01_MORNING_BRIEF.md")
    for candidate in candidates:
        try:
            write_memory_candidate(candidate)
            result.memory_candidates += 1
            if persist_to_db:
                _maybe_save_memory_candidate(candidate, errors=result.errors)
        except Exception as exc:  # pragma: no cover - obsidian write issues
            result.errors.append(f"Memory candidate write failed: {exc}")

    # --- Update packet status + close run ---------------------------
    final_status = (
        "COMPLETED" if result.files_failed == 0 else "PARTIAL_FAILURE"
    )
    result.status = final_status
    result.completed_at = datetime.now(UTC)

    if persist_to_db:
        _maybe_update_packet_status(str(packet.id), final_status, result.errors)
        _maybe_complete_execution_run(
            run_id_str,
            status="COMPLETED" if final_status == "COMPLETED" else "FAILED",
            errors=result.errors,
        )

    return result


def run_all_ready_packets(
    *,
    mode: str = "NIGHT_MODE",
    manual_override: bool = False,
    backend: LLMBackend | None = None,
    cfg: AssistantConfig | None = None,
    day: date | None = None,
) -> list[ExecutionResult]:
    """Run execution for every packet currently in a READY_* status.

    Used by the overnight runner and the Temporal workflow's activity body.
    Returns one ExecutionResult per packet.
    """
    cfg = cfg or load_assistant_config()
    packet_ids = _maybe_load_ready_packet_ids()
    if not packet_ids:
        empty = ExecutionResult(
            work_packet_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
            status="NO_PACKETS",
        )
        empty.errors.append("No READY_FOR_OVERNIGHT or READY_HIGH_CONFIDENCE packets found.")
        empty.completed_at = datetime.now(UTC)
        return [empty]
    return [
        run_execution_for_packet(
            work_packet_id=pid,
            mode=mode,
            manual_override=manual_override,
            backend=backend,
            cfg=cfg,
            day=day,
        )
        for pid in packet_ids
    ]


# ---------------------------------------------------------------------------
# Internals: per-source processing
# ---------------------------------------------------------------------------

def _process_one_source(
    *,
    source_path: str,
    packet: WorkPacket,
    mode: str,
    manual_override: bool,
    backend: LLMBackend,
    cfg: AssistantConfig,
    run_id_str: str | None,
    result: ExecutionResult,
    persist_to_db: bool,
) -> tuple[FileExecutionRecord, str | None]:
    record = FileExecutionRecord(
        file_path=source_path,
        classified_as="general",
        primary_model_group=PRIMARY_GROUP,
    )
    record.primary_model_tag = _resolve_tag_for_group(PRIMARY_GROUP)

    # Load file content
    try:
        loaded = load_supported_file(source_path)
    except UnsupportedFileType as exc:
        record.error = f"unsupported file type: {exc}"
        return record, None
    except FileNotFoundError as exc:
        record.error = f"file not found: {exc}"
        return record, None
    except Exception as exc:  # pragma: no cover - defensive
        record.error = f"load failed: {exc}"
        return record, None

    kind = loaded.get("kind", "unknown")
    content = loaded.get("content") or _format_csv_preview(loaded)
    if content is None:
        record.error = "empty content"
        return record, None

    record.bytes_in = len(content)
    chunks = chunk_text(content, cfg.max_chars_per_chunk)
    record.chunks_processed = len(chunks)

    # Per-chunk extraction (v1: one extraction per file using the first chunk
    # plus a note about additional chunks. Multi-chunk synthesis is a v2 task.)
    primary_content = chunks[0]
    if len(chunks) > 1:
        primary_content = (
            primary_content
            + f"\n\n[NOTE: source had {len(chunks)} chunks of "
            f"{cfg.max_chars_per_chunk} chars; only the first is shown here.]"
        )

    prompt = format_extract_prompt(
        packet=packet,
        source_path=source_path,
        kind=kind,
        content=primary_content,
    )

    # Primary call
    try:
        response = backend(PRIMARY_GROUP, prompt, mode, manual_override)
    except SafetyError as exc:
        record.error = f"safety gate: {exc}"
        _maybe_log_model_call(
            run_id_str=run_id_str,
            work_packet_id=str(packet.id),
            file_path=source_path,
            task_type="extract",
            model_group=PRIMARY_GROUP,
            actual_model=record.primary_model_tag,
            local_or_cloud="local",
            prompt_chars=len(prompt),
            response_chars=0,
            success=False,
            error=str(exc),
            errors=result.errors,
            persist=persist_to_db,
        )
        return record, None
    except Exception as exc:
        record.error = f"primary model failed: {exc}"
        _maybe_log_model_call(
            run_id_str=run_id_str,
            work_packet_id=str(packet.id),
            file_path=source_path,
            task_type="extract",
            model_group=PRIMARY_GROUP,
            actual_model=record.primary_model_tag,
            local_or_cloud="local",
            prompt_chars=len(prompt),
            response_chars=0,
            success=False,
            error=str(exc),
            errors=result.errors,
            persist=persist_to_db,
        )
        return record, None

    record.chars_out = len(response)
    result.model_calls += 1
    _maybe_log_model_call(
        run_id_str=run_id_str,
        work_packet_id=str(packet.id),
        file_path=source_path,
        task_type="extract",
        model_group=PRIMARY_GROUP,
        actual_model=record.primary_model_tag,
        local_or_cloud="local",
        prompt_chars=len(prompt),
        response_chars=len(response),
        success=True,
        error=None,
        errors=result.errors,
        persist=persist_to_db,
    )

    # Evaluate the response deterministically
    evaluation = deterministic_completeness_evaluator(response, EVAL_REQUIRED_TERMS)
    record.evaluation_passed = bool(evaluation.pass_)
    _maybe_save_evaluation(
        evaluation=evaluation,
        run_id_str=run_id_str,
        work_packet_id=str(packet.id),
        file_path=source_path,
        errors=result.errors,
        persist=persist_to_db,
    )

    return record, response


# ---------------------------------------------------------------------------
# Internals: synthesis + outputs
# ---------------------------------------------------------------------------

def _synthesize_brief(
    *,
    packet: WorkPacket,
    extractions: list[tuple[str, str]],
    today: str,
    mode: str,
    manual_override: bool,
    backend: LLMBackend,
    run_id_str: str | None,
    result: ExecutionResult,
    persist_to_db: bool,
) -> str:
    blocks = []
    for path, text in extractions:
        blocks.append(f"=== Extraction from: {path} ===\n{text.strip()}\n")
    prompt = format_synthesize_prompt(
        packet=packet,
        extractions="\n".join(blocks),
        today=today,
    )

    try:
        brief = backend(PRIMARY_GROUP, prompt, mode, manual_override)
    except Exception as exc:
        result.errors.append(f"synthesis failed: {exc}")
        # Fall back to a deterministic concatenation so the run still produces
        # something useful instead of returning nothing.
        return _fallback_brief(today, extractions)

    result.model_calls += 1
    _maybe_log_model_call(
        run_id_str=run_id_str,
        work_packet_id=str(packet.id),
        file_path=None,
        task_type="synthesize",
        model_group=PRIMARY_GROUP,
        actual_model=_resolve_tag_for_group(PRIMARY_GROUP),
        local_or_cloud="local",
        prompt_chars=len(prompt),
        response_chars=len(brief),
        success=True,
        error=None,
        errors=result.errors,
        persist=persist_to_db,
    )
    return brief


def _write_outputs(
    *,
    output_dir: Path,
    packet: WorkPacket,
    brief_md: str,
    extractions: list[tuple[str, str]],
    run_id_str: str | None,
    result: ExecutionResult,
    persist_to_db: bool,
) -> None:
    # 00_STATUS.json
    status = {
        "work_packet_id": str(packet.id),
        "title": packet.title,
        "files_processed": result.files_processed,
        "files_failed": result.files_failed,
        "model_calls": result.model_calls,
        "errors": list(result.errors),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    status_path = write_status(output_dir, status)
    _record_artifact(
        status_path,
        artifact_type="status",
        packet_id=str(packet.id),
        run_id_str=run_id_str,
        result=result,
        persist=persist_to_db,
    )

    # 01_MORNING_BRIEF.md
    brief_path = output_dir / "01_MORNING_BRIEF.md"
    brief_path.write_text(brief_md.strip() + "\n", encoding="utf-8")
    _record_artifact(
        brief_path,
        artifact_type="morning_brief",
        packet_id=str(packet.id),
        run_id_str=run_id_str,
        result=result,
        persist=persist_to_db,
    )

    # 09_AUDIT_LOG.md
    audit_lines = [
        f"# Audit log",
        "",
        f"Work packet: {packet.id}",
        f"Title: {packet.title}",
        f"Files processed: {result.files_processed}",
        f"Files failed: {result.files_failed}",
        f"Model calls: {result.model_calls}",
        f"Status: {result.status}",
        "",
        "## Per-file outcomes",
    ]
    for rec in result.file_records:
        audit_lines.append(
            f"- `{rec.file_path}` -> "
            f"chunks={rec.chunks_processed} bytes_in={rec.bytes_in} "
            f"chars_out={rec.chars_out} "
            f"eval_pass={rec.evaluation_passed} "
            f"error={rec.error or '(none)'}"
        )
    audit_path = output_dir / "09_AUDIT_LOG.md"
    audit_path.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")
    _record_artifact(
        audit_path,
        artifact_type="audit_log",
        packet_id=str(packet.id),
        run_id_str=run_id_str,
        result=result,
        persist=persist_to_db,
    )

    # Per-file extraction dumps (for debugging / reproducibility)
    extracts_dir = output_dir / "_extractions"
    extracts_dir.mkdir(parents=True, exist_ok=True)
    for path, text in extractions:
        safe = Path(path).name.replace("/", "_").replace(":", "_")
        target = extracts_dir / f"{safe}.md"
        target.write_text(text.strip() + "\n", encoding="utf-8")
        _record_artifact(
            target,
            artifact_type="extraction",
            packet_id=str(packet.id),
            run_id_str=run_id_str,
            result=result,
            persist=persist_to_db,
        )


# ---------------------------------------------------------------------------
# Internals: storage glue (best-effort; degrade gracefully)
# ---------------------------------------------------------------------------

def _load_packet_or_raise(packet_id: str) -> WorkPacket:
    from assistant_core.storage import StorageUnavailable, get_work_packet

    try:
        return get_work_packet(packet_id)
    except StorageUnavailable as exc:
        raise RuntimeError(
            f"Cannot load packet {packet_id}: {exc}. "
            "Pass packet=WorkPacket(...) directly if you intend to run without DB."
        ) from exc


def _maybe_load_ready_packet_ids() -> list[str]:
    from assistant_core.storage import StorageUnavailable, ready_work_packet_ids

    try:
        return ready_work_packet_ids()
    except StorageUnavailable:
        return []


def _maybe_create_execution_run(
    *, work_packet_id: str, mode: str, errors: list[str]
) -> str | None:
    from assistant_core.storage import StorageUnavailable, create_execution_run

    try:
        return create_execution_run(work_packet_id, mode=mode, status="RUNNING")
    except StorageUnavailable as exc:
        errors.append(f"could not record execution_run start: {exc}")
        return None


def _maybe_complete_execution_run(
    run_id_str: str | None, *, status: str, errors: list[str]
) -> None:
    if run_id_str is None:
        return
    from assistant_core.storage import StorageUnavailable, complete_execution_run

    summary = "; ".join(errors[-3:]) if errors else None
    try:
        complete_execution_run(run_id_str, status=status, error_summary=summary)
    except StorageUnavailable as exc:
        errors.append(f"could not finalize execution_run: {exc}")


def _maybe_log_model_call(
    *,
    run_id_str: str | None,
    work_packet_id: str,
    file_path: str | None,
    task_type: str,
    model_group: str,
    actual_model: str | None,
    local_or_cloud: str,
    prompt_chars: int,
    response_chars: int,
    success: bool,
    error: str | None,
    errors: list[str],
    persist: bool,
) -> None:
    if not persist:
        return
    from uuid import UUID

    from assistant_core.storage import StorageUnavailable, log_model_call

    try:
        log_model_call(
            ModelCallLog(
                execution_run_id=UUID(run_id_str) if run_id_str else None,
                work_packet_id=UUID(work_packet_id),
                file_path=file_path,
                task_type=task_type,
                model_group=model_group,
                actual_model=actual_model,
                local_or_cloud="local" if local_or_cloud != "cloud" else "cloud",
                prompt_chars=prompt_chars,
                response_chars=response_chars,
                success=success,
                error=error,
            )
        )
    except StorageUnavailable as exc:
        errors.append(f"could not log model_call: {exc}")


def _maybe_save_evaluation(
    *,
    evaluation,
    run_id_str: str | None,
    work_packet_id: str,
    file_path: str | None,
    errors: list[str],
    persist: bool,
) -> None:
    if not persist:
        return
    from assistant_core.storage import StorageUnavailable, save_evaluation

    try:
        save_evaluation(
            evaluation,
            execution_run_id=run_id_str,
            work_packet_id=work_packet_id,
            file_path=file_path,
        )
    except StorageUnavailable as exc:
        errors.append(f"could not save evaluation: {exc}")


def _maybe_save_memory_candidate(
    candidate: MemoryCandidate, *, errors: list[str]
) -> None:
    from assistant_core.storage import StorageUnavailable, save_memory_candidate

    try:
        save_memory_candidate(candidate)
    except StorageUnavailable as exc:
        errors.append(f"could not save memory candidate: {exc}")


def _maybe_update_packet_status(
    work_packet_id: str, status: str, errors: list[str]
) -> None:
    from assistant_core.storage import StorageUnavailable, update_work_packet_status

    try:
        update_work_packet_status(work_packet_id, status)
    except StorageUnavailable as exc:
        errors.append(f"could not update packet status: {exc}")


def _record_artifact(
    file_path: Path,
    *,
    artifact_type: str,
    packet_id: str,
    run_id_str: str | None,
    result: ExecutionResult,
    persist: bool,
) -> None:
    result.artifacts_written += 1
    if not persist:
        return
    from uuid import UUID

    from assistant_core.storage import StorageUnavailable, save_artifact

    artifact = Artifact(
        execution_run_id=UUID(run_id_str) if run_id_str else None,
        work_packet_id=UUID(packet_id),
        artifact_type=artifact_type,
        file_path=file_path,
    )
    try:
        save_artifact(artifact)
    except StorageUnavailable as exc:
        result.errors.append(f"could not save artifact: {exc}")


# ---------------------------------------------------------------------------
# Internals: misc helpers
# ---------------------------------------------------------------------------

def _scan_sources(packet: WorkPacket, *, errors: list[str]) -> list[str]:
    """Resolve packet.source_paths into a flat list of supported files."""
    results: list[str] = []
    seen: set[str] = set()

    for entry in packet.source_paths:
        try:
            resolved = resolve_user_path(entry)
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"could not resolve {entry!r}: {exc}")
            continue
        if not resolved.exists():
            errors.append(f"source path does not exist: {resolved}")
            continue
        if resolved.is_file():
            _maybe_add(results, seen, resolved)
        elif resolved.is_dir():
            for path in sorted(resolved.rglob("*")):
                if path.is_file():
                    _maybe_add(results, seen, path)
    return results


def _maybe_add(out: list[str], seen: set[str], path: Path) -> None:
    if path.suffix.lower() not in {".txt", ".md", ".csv", ".json", ".log"}:
        return
    s = str(path)
    if s in seen:
        return
    seen.add(s)
    out.append(s)


def _format_csv_preview(loaded: dict[str, Any]) -> str:
    profile = loaded.get("profile", {})
    columns = profile.get("columns", [])
    rows = profile.get("preview_rows", [])
    lines = [f"CSV: {len(columns)} columns, {profile.get('row_count', 0)} rows"]
    lines.append("Columns: " + ", ".join(map(str, columns)))
    lines.append("First rows:")
    for row in rows[:10]:
        lines.append(f"  - {row}")
    return "\n".join(lines)


def _resolve_tag_for_group(group: str) -> str | None:
    mapping = ollama_admin.tag_to_group_mapping()
    reverse = {g: t for t, g in mapping.items()}
    return reverse.get(group)


def _fallback_brief(today: str, extractions: list[tuple[str, str]]) -> str:
    lines = [
        f"# Morning Brief - {today}",
        "",
        "_Synthesis model call failed. This is a deterministic fallback._",
        "",
    ]
    for path, text in extractions:
        lines.append(f"## From {path}")
        lines.append(text.strip())
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "PRIMARY_GROUP",
    "SECONDARY_GROUP",
    "run_execution_for_packet",
    "run_all_ready_packets",
]
