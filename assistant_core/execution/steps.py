"""Pipeline steps. One function per step. Each step's signature is
``StepContext -> StepContext``.

To add a step:
    1. Write a function below following the established docstring shape.
    2. Add it to EXECUTION_GRAPH in ``execution/graph.py``.

To remove or reorder a step:
    Edit EXECUTION_GRAPH in ``execution/graph.py``. Step functions stay here.

To test a step in isolation:
    Build a minimal StepContext, call the step, assert mutations on
    ``ctx.result`` or ``ctx.<field>``.

Steps SHOULD:
    - Be small and single-purpose.
    - Mutate ``ctx`` rather than return a new one (return the same ctx).
    - Set ``ctx.halt = True`` when the pipeline cannot meaningfully continue.
    - Append human-readable strings to ``ctx.result.errors`` rather than raise,
      unless the failure is catastrophic.
    - Be idempotent where possible (re-running a step shouldn't double-write).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from assistant_core.execution.context import StepContext
from assistant_core.execution.evaluators import deterministic_completeness_evaluator
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
from assistant_core.paths import resolve_user_path
from assistant_core.safety import (
    SafetyError,
    assert_cloud_allowed,
    assert_heavy_execution_allowed,
)
from assistant_core.schemas import (
    Artifact,
    CloudCandidate,
    FileExecutionRecord,
    MemoryCandidate,
    ModelCallLog,
)


logger = logging.getLogger(__name__)


# Constants used by extract / synthesize steps
PRIMARY_GROUP = "local-main"
SECONDARY_GROUP = "local-secondary"
REASONER_GROUP = "local-reasoner"
CODER_GROUP = "local-coder"
EVAL_REQUIRED_TERMS = ["priorities", "decisions", "risks"]
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}

# File extensions that should route to the coder model instead of local-main.
# When the panel's Models tab lets the user pull qwen3-coder, code work goes
# there automatically. If qwen3-coder isn't pulled, the secondary retry chain
# still catches quality issues.
CODE_EXTENSIONS = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
     ".cpp", ".cxx", ".cc", ".c", ".h", ".hpp", ".rb", ".swift", ".kt",
     ".scala", ".php", ".sql", ".sh", ".bash"}
)

# Tasks that map to which model group for the primary attempt.
TASK_TO_PRIMARY_GROUP = {
    "general": PRIMARY_GROUP,
    "coding": CODER_GROUP,
    "reasoning": REASONER_GROUP,
}


# =============================================================================
# Top-level pipeline steps
# =============================================================================


def safety_gate(ctx: StepContext) -> StepContext:
    """Refuse to proceed when the mode does not permit local model execution.

    DAY_MODE blocks unless ``manual_override=True`` or the day-unlock flag is
    active. NIGHT_MODE and MANUAL_RESUME always pass.
    """
    try:
        assert_heavy_execution_allowed(ctx.mode, manual_override=ctx.manual_override)
    except SafetyError as exc:
        ctx.result.status = "BLOCKED_BY_SAFETY"
        ctx.result.errors.append(f"Safety gate refused execution: {exc}")
        ctx.halt = True
    return ctx


def initialize_run(ctx: StepContext) -> StepContext:
    """Best-effort: create an execution_runs row in Postgres so the run is auditable.

    Skipped when ``persist_to_db`` is False or Postgres is unreachable. Errors
    do NOT halt the pipeline; we proceed to filesystem-only outputs.
    """
    if not ctx.persist_to_db:
        return ctx
    from assistant_core.storage import StorageUnavailable, create_execution_run

    try:
        run_id = create_execution_run(
            str(ctx.packet.id), mode=ctx.mode, status="RUNNING"
        )
        ctx.run_id_str = run_id
        ctx.result.execution_run_id = UUID(run_id)
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not record execution_run start: {exc}")
    return ctx


def scan_sources(ctx: StepContext) -> StepContext:
    """Resolve ``packet.source_paths`` into a flat list of supported files.

    Walks directories recursively; keeps only files whose suffix is in
    SUPPORTED_EXTENSIONS. Halts with NO_SOURCES if no supported files are found.
    """
    seen: set[str] = set()
    for entry in ctx.packet.source_paths:
        try:
            resolved = resolve_user_path(entry)
        except Exception as exc:  # pragma: no cover - defensive
            ctx.result.errors.append(f"could not resolve {entry!r}: {exc}")
            continue
        if not resolved.exists():
            ctx.result.errors.append(f"source path does not exist: {resolved}")
            continue
        if resolved.is_file():
            _maybe_add_source(ctx.source_files, seen, resolved)
        elif resolved.is_dir():
            for path in sorted(resolved.rglob("*")):
                if path.is_file():
                    _maybe_add_source(ctx.source_files, seen, path)

    if not ctx.source_files:
        ctx.result.status = "NO_SOURCES"
        ctx.result.errors.append(
            "No supported source files found under packet.source_paths"
        )
        ctx.halt = True
        _finalize_run_row(ctx, db_status="FAILED")
    return ctx


def process_sources(ctx: StepContext) -> StepContext:
    """For each source file: load, chunk, extract via primary model, evaluate.

    Internally walks the substeps for one source:
        load_file -> classify_file_task -> privacy_gate (already done in
        scan_sources) -> chunk_content -> execute_primary_local ->
        evaluate_primary -> [execute_secondary_local_if_needed: scaffold] ->
        [reasoning_check_if_needed: scaffold].

    Per-file errors do NOT halt the pipeline; they are recorded on the
    FileExecutionRecord and counted in files_failed.
    """
    for source_path in ctx.source_files:
        record, extraction = _process_one_source(ctx, source_path)
        ctx.result.file_records.append(record)
        if record.error is None and extraction is not None:
            ctx.extractions.append((source_path, extraction))
            ctx.result.files_processed += 1
        else:
            ctx.result.files_failed += 1

    if not ctx.extractions:
        ctx.result.status = "PARTIAL_FAILURE"
        ctx.result.completed_at = datetime.now(UTC)
        ctx.halt = True
        _finalize_run_row(ctx, db_status="FAILED")
    return ctx


def cloud_review_gate(ctx: StepContext) -> StepContext:
    """Catalog files that local execution flagged for cloud review.

    For each record with ``needs_cloud_review=True``:
      1. Run it through ``assert_cloud_allowed`` with the current config.
      2. Record a CloudCandidate on ``ctx.result.cloud_candidates`` capturing
         the gate's verdict (allowed / blocked-with-reason).
      3. When the gate allows it AND a cloud caller is wired, escalate.
         Today no cloud caller is wired (deliberate default-off), so we
         set ``escalated=False`` and 0 cost, and let the user wire the
         actual call later by setting cloud_fallback_enabled + key + budget.

    The 08_CLOUD_REVIEW_CANDIDATES.md output is written from the candidates
    list during ``write_outputs`` so the user can see what would have
    escalated without enabling any cloud spend.
    """
    flagged = [r for r in ctx.result.file_records if r.needs_cloud_review]
    if not flagged:
        return ctx

    cfg = ctx.cfg
    cloud_review_dir = cfg.inbox_dir / "cloud_review"

    for record in flagged:
        candidate = CloudCandidate(
            file_path=record.file_path,
            reason="primary and secondary local extractions failed the evaluator",
            primary_model_group=record.primary_model_group,
            secondary_model_group=record.secondary_model_group,
        )

        block_reason: str | None = None
        try:
            assert_cloud_allowed(
                file_path=record.file_path,
                cloud_fallback_enabled=cfg.cloud_fallback_enabled,
                work_packet_cloud_allowed=bool(
                    ctx.packet.cloud_policy.get("allowed", False)
                ),
                high_stakes=ctx.packet.high_stakes,
                local_quality_gate_failed=True,
                anthropic_api_key=_anthropic_key_present(),
                daily_budget_remaining=True,
                cloud_review_dir=cloud_review_dir,
            )
            candidate.gate_passed = True
        except SafetyError as exc:
            block_reason = str(exc)
            candidate.gate_passed = False
            candidate.gate_block_reason = block_reason

        # When the gate passes, escalation is policy-allowed. The actual HTTP
        # call to Claude is left for a follow-up commit (no caller wired yet)
        # so this default-off path never spends a token.
        if candidate.gate_passed:
            # Caller wiring lives here later. For now: mark we'd have called.
            candidate.escalated = False
            candidate.cloud_response_chars = 0
            candidate.estimated_cost_usd = None

        ctx.result.cloud_candidates.append(candidate)

    ctx.result.cloud_candidates_logged = len(ctx.result.cloud_candidates)
    ctx.result.cloud_calls_made = sum(
        1 for c in ctx.result.cloud_candidates if c.escalated
    )
    return ctx


def _anthropic_key_present() -> str | None:
    """Return ANTHROPIC_API_KEY if set (any value), else None.

    Pulled out so tests can monkeypatch via os.environ.
    """
    import os

    return os.environ.get("ANTHROPIC_API_KEY") or None


def synthesize_brief(ctx: StepContext) -> StepContext:
    """Compose all per-file extractions into a single morning brief via the
    primary model. If synthesis fails, falls back to a deterministic
    concatenation so the run still produces a brief."""
    blocks = [
        f"=== Extraction from: {path} ===\n{text.strip()}\n"
        for path, text in ctx.extractions
    ]
    prompt = format_synthesize_prompt(
        packet=ctx.packet,
        extractions="\n".join(blocks),
        today=ctx.day.isoformat(),
    )
    try:
        brief = ctx.backend(PRIMARY_GROUP, prompt, ctx.mode, ctx.manual_override)
    except Exception as exc:
        ctx.result.errors.append(f"synthesis failed: {exc}")
        ctx.brief_md = _fallback_brief(ctx.day.isoformat(), ctx.extractions)
        return ctx

    ctx.result.model_calls += 1
    _maybe_log_model_call(
        ctx,
        file_path=None,
        task_type="synthesize",
        model_group=PRIMARY_GROUP,
        actual_model=_tag_for_group(PRIMARY_GROUP),
        prompt_chars=len(prompt),
        response_chars=len(brief),
        success=True,
        error=None,
    )
    ctx.brief_md = brief
    return ctx


def write_outputs(ctx: StepContext) -> StepContext:
    """Write 00_STATUS.json, 01_MORNING_BRIEF.md, 09_AUDIT_LOG.md, and
    per-file extraction dumps to ~/LocalAI/output/<date>/."""
    output_dir = dated_output_dir(ctx.cfg, day=ctx.day)
    ctx.output_dir = output_dir
    ctx.result.output_dir = str(output_dir)

    # 00_STATUS.json
    status_payload = {
        "work_packet_id": str(ctx.packet.id),
        "title": ctx.packet.title,
        "files_processed": ctx.result.files_processed,
        "files_failed": ctx.result.files_failed,
        "model_calls": ctx.result.model_calls,
        "errors": list(ctx.result.errors),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    status_path = write_status(output_dir, status_payload)
    _record_artifact(ctx, status_path, artifact_type="status")

    # 01_MORNING_BRIEF.md
    brief_path = output_dir / "01_MORNING_BRIEF.md"
    brief_path.write_text(ctx.brief_md.strip() + "\n", encoding="utf-8")
    _record_artifact(ctx, brief_path, artifact_type="morning_brief")

    # 09_AUDIT_LOG.md
    audit_lines = [
        "# Audit log",
        "",
        f"Work packet: {ctx.packet.id}",
        f"Title: {ctx.packet.title}",
        f"Files processed: {ctx.result.files_processed}",
        f"Files failed: {ctx.result.files_failed}",
        f"Model calls: {ctx.result.model_calls}",
        f"Status: {ctx.result.status}",
        "",
        "## Per-file outcomes",
    ]
    for rec in ctx.result.file_records:
        audit_lines.append(
            f"- `{rec.file_path}` -> "
            f"chunks={rec.chunks_processed} bytes_in={rec.bytes_in} "
            f"chars_out={rec.chars_out} "
            f"eval_pass={rec.evaluation_passed} "
            f"error={rec.error or '(none)'}"
        )
    audit_path = output_dir / "09_AUDIT_LOG.md"
    audit_path.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")
    _record_artifact(ctx, audit_path, artifact_type="audit_log")

    # 08_CLOUD_REVIEW_CANDIDATES.md (always written so the user can see
    # what local execution couldn't handle, regardless of whether cloud
    # was enabled this run).
    _write_cloud_candidates_file(ctx, output_dir)

    # Per-file extraction dumps for debugging / reproducibility
    extracts_dir = output_dir / "_extractions"
    extracts_dir.mkdir(parents=True, exist_ok=True)
    for path, text in ctx.extractions:
        safe = Path(path).name.replace("/", "_").replace(":", "_")
        target = extracts_dir / f"{safe}.md"
        target.write_text(text.strip() + "\n", encoding="utf-8")
        _record_artifact(ctx, target, artifact_type="extraction")

    return ctx


def _write_cloud_candidates_file(ctx: StepContext, output_dir: Path) -> None:
    """Render the cloud-review catalog as Markdown.

    The file is always written; an empty candidates list produces an
    explicit "(none)" entry. This lets you grep your output history for
    when cloud was ever considered.
    """
    candidates = ctx.result.cloud_candidates
    lines = [
        "# Cloud Review Candidates",
        "",
        f"Work packet: {ctx.packet.id}",
        f"Title: {ctx.packet.title}",
        "",
    ]
    if not candidates:
        lines.append("No files were flagged for cloud review in this run.")
    else:
        lines.append(
            f"{len(candidates)} file(s) flagged. "
            f"{sum(1 for c in candidates if c.gate_passed)} passed the safety gate; "
            f"{sum(1 for c in candidates if c.escalated)} actually called cloud."
        )
        lines.append("")
        for candidate in candidates:
            lines.append(f"## `{candidate.file_path}`")
            lines.append(f"- Reason: {candidate.reason}")
            lines.append(f"- Tried locally: {candidate.primary_model_group}"
                         + (f" -> {candidate.secondary_model_group}"
                            if candidate.secondary_model_group else ""))
            lines.append(
                f"- Safety gate: {'PASSED' if candidate.gate_passed else 'BLOCKED'}"
            )
            if candidate.gate_block_reason:
                lines.append(f"- Block reason: {candidate.gate_block_reason}")
            lines.append(
                f"- Escalated to cloud: {'yes' if candidate.escalated else 'no'}"
            )
            if candidate.escalated:
                lines.append(f"- Cloud response chars: {candidate.cloud_response_chars}")
                if candidate.estimated_cost_usd is not None:
                    lines.append(
                        f"- Estimated cost: ${candidate.estimated_cost_usd:.4f}"
                    )
            lines.append("")

    target = output_dir / "08_CLOUD_REVIEW_CANDIDATES.md"
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    _record_artifact(ctx, target, artifact_type="cloud_review_candidates")


def write_obsidian(ctx: StepContext) -> StepContext:
    """Copy the morning brief into ~/Obsidian/LocalAI-ChiefOfStaff/01_Daily_Briefs/."""
    try:
        obsidian_path = write_daily_brief(ctx.brief_md, cfg=None, day=ctx.day)
        ctx.result.obsidian_brief_path = str(obsidian_path)
    except Exception as exc:  # pragma: no cover - obsidian path issues
        ctx.result.errors.append(f"Obsidian write failed: {exc}")
    return ctx


def generate_memory_candidates(ctx: StepContext) -> StepContext:
    """Extract memory candidates from the brief, write them into the Memory_Review
    queue, and (best-effort) persist to Postgres for the reviewer flow."""
    candidates = extract_memory_candidates(
        ctx.brief_md, source_path="01_MORNING_BRIEF.md"
    )
    for candidate in candidates:
        try:
            write_memory_candidate(candidate)
            ctx.result.memory_candidates += 1
            if ctx.persist_to_db:
                _maybe_save_memory_candidate(ctx, candidate)
        except Exception as exc:  # pragma: no cover - obsidian write issues
            ctx.result.errors.append(f"Memory candidate write failed: {exc}")
    return ctx


def archive_processed_files(ctx: StepContext) -> StepContext:
    """Scaffolded. Will move consumed inputs from ~/LocalAI/inbox/ to
    ~/LocalAI/archive/<date>/ once we have a confirmed-success contract.
    Today a no-op so re-runs against the same inputs remain idempotent."""
    return ctx


def finalize_run(ctx: StepContext) -> StepContext:
    """Set the final ExecutionResult.status, update work_packets row, and close
    the execution_runs row in Postgres."""
    final_status = "COMPLETED" if ctx.result.files_failed == 0 else "PARTIAL_FAILURE"
    ctx.result.status = final_status
    ctx.result.completed_at = datetime.now(UTC)
    if ctx.persist_to_db:
        _maybe_update_packet_status(ctx, final_status)
        _finalize_run_row(
            ctx,
            db_status="COMPLETED" if final_status == "COMPLETED" else "FAILED",
        )
    return ctx


# =============================================================================
# Per-source sub-steps (called from process_sources, not directly in the graph)
#
# These mirror the documented inner steps from EXECUTION_STEPS:
#   load_file -> classify_file_task -> privacy_gate (handled in scan_sources)
#   -> chunk_content -> execute_primary_local -> evaluate_primary
#   -> execute_secondary_local_if_needed (scaffold) -> reasoning_check_if_needed (scaffold)
# =============================================================================


def _process_one_source(
    ctx: StepContext, source_path: str
) -> tuple[FileExecutionRecord, str | None]:
    """Run the per-source sub-pipeline for one file. Returns (record, extraction)."""
    record = FileExecutionRecord(file_path=source_path)

    # --- load_file -----------------------------------------------------
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

    # --- classify_file_task -------------------------------------------
    task_type, primary_group = _classify_task(loaded)
    record.classified_as = task_type
    record.primary_model_group = primary_group
    record.primary_model_tag = _tag_for_group(primary_group)

    kind = loaded.get("kind", "unknown")
    content = loaded.get("content") or _format_csv_preview(loaded)
    if content is None:
        record.error = "empty content"
        return record, None

    # --- chunk_content ------------------------------------------------
    record.bytes_in = len(content)
    chunks = chunk_text(content, ctx.cfg.max_chars_per_chunk)
    record.chunks_processed = len(chunks)
    primary_content = chunks[0]
    if len(chunks) > 1:
        primary_content = (
            primary_content
            + f"\n\n[NOTE: source had {len(chunks)} chunks of "
            f"{ctx.cfg.max_chars_per_chunk} chars; only the first is shown here.]"
        )

    # --- execute_primary_local + evaluate ----------------------------
    prompt = format_extract_prompt(
        packet=ctx.packet,
        source_path=source_path,
        kind=kind,
        content=primary_content,
    )
    primary_response, primary_error = _call_extract(
        ctx, primary_group, prompt, source_path, record.primary_model_tag
    )
    if primary_response is None:
        record.error = primary_error
        return record, None

    record.chars_out = len(primary_response)
    evaluation = deterministic_completeness_evaluator(
        primary_response, EVAL_REQUIRED_TERMS
    )
    record.evaluation_passed = bool(evaluation.pass_)
    _maybe_save_evaluation(ctx, evaluation=evaluation, file_path=source_path)

    if record.evaluation_passed:
        return record, primary_response

    # --- execute_secondary_local_if_needed ---------------------------
    # Primary output failed the evaluator. Retry on local-secondary (70B)
    # unless the primary already WAS the secondary group, or budget says no.
    if (
        SECONDARY_GROUP != primary_group
        and ctx.cfg.max_local_attempts >= 2
    ):
        record.retry_attempted = True
        record.secondary_model_group = SECONDARY_GROUP
        record.secondary_model_tag = _tag_for_group(SECONDARY_GROUP)
        secondary_response, _ = _call_extract(
            ctx, SECONDARY_GROUP, prompt, source_path, record.secondary_model_tag
        )
        if secondary_response is not None:
            record.secondary_chars_out = len(secondary_response)
            sec_eval = deterministic_completeness_evaluator(
                secondary_response, EVAL_REQUIRED_TERMS
            )
            _maybe_save_evaluation(
                ctx, evaluation=sec_eval, file_path=source_path
            )
            if sec_eval.pass_:
                record.retry_succeeded = True
                record.evaluation_passed = True
                return record, secondary_response
            # Secondary also failed; we still prefer its output as the
            # extraction (more capable model), and mark cloud-review.
            record.needs_cloud_review = True
            return record, secondary_response

    # Either secondary was skipped (budget/policy) or it didn't produce a
    # response. Flag for cloud review and return the primary output.
    record.needs_cloud_review = True
    return record, primary_response


def _call_extract(
    ctx: StepContext,
    model_group: str,
    prompt: str,
    source_path: str,
    actual_tag: str | None,
) -> tuple[str | None, str | None]:
    """Single extraction call against ``model_group``.

    Returns ``(response_or_None, error_or_None)``. Logs the model call to
    Postgres on both success and failure. Pulled out of _process_one_source
    so primary and secondary attempts share exactly one path.
    """
    try:
        response = ctx.backend(model_group, prompt, ctx.mode, ctx.manual_override)
    except SafetyError as exc:
        _maybe_log_model_call(
            ctx,
            file_path=source_path,
            task_type="extract",
            model_group=model_group,
            actual_model=actual_tag,
            prompt_chars=len(prompt),
            response_chars=0,
            success=False,
            error=str(exc),
        )
        return None, f"safety gate ({model_group}): {exc}"
    except Exception as exc:
        _maybe_log_model_call(
            ctx,
            file_path=source_path,
            task_type="extract",
            model_group=model_group,
            actual_model=actual_tag,
            prompt_chars=len(prompt),
            response_chars=0,
            success=False,
            error=str(exc),
        )
        return None, f"{model_group} model failed: {exc}"

    ctx.result.model_calls += 1
    _maybe_log_model_call(
        ctx,
        file_path=source_path,
        task_type="extract",
        model_group=model_group,
        actual_model=actual_tag,
        prompt_chars=len(prompt),
        response_chars=len(response),
        success=True,
        error=None,
    )
    return response, None


# =============================================================================
# Helpers (private; not part of the step graph)
# =============================================================================


def _classify_task(loaded: dict[str, Any]) -> tuple[str, str]:
    """Return (task_type, primary_model_group) for a loaded source file.

    Today's heuristics:
      - any code file extension -> ('coding', local-coder)
      - everything else -> ('general', local-main)

    Future: inspect content for reasoning-heavy patterns (multi-hop
    questions, contradiction analysis) and route to local-reasoner.
    """
    suffix = Path(loaded.get("path", "")).suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return "coding", CODER_GROUP
    return "general", PRIMARY_GROUP


def _maybe_add_source(out: list[str], seen: set[str], path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
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


def _tag_for_group(group: str) -> str | None:
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


def _record_artifact(
    ctx: StepContext, file_path: Path, *, artifact_type: str
) -> None:
    ctx.result.artifacts_written += 1
    if not ctx.persist_to_db:
        return
    from assistant_core.storage import StorageUnavailable, save_artifact

    artifact = Artifact(
        execution_run_id=UUID(ctx.run_id_str) if ctx.run_id_str else None,
        work_packet_id=ctx.packet.id,
        artifact_type=artifact_type,
        file_path=file_path,
    )
    try:
        save_artifact(artifact)
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not save artifact: {exc}")


def _maybe_log_model_call(
    ctx: StepContext,
    *,
    file_path: str | None,
    task_type: str,
    model_group: str,
    actual_model: str | None,
    prompt_chars: int,
    response_chars: int,
    success: bool,
    error: str | None,
) -> None:
    if not ctx.persist_to_db:
        return
    from assistant_core.storage import StorageUnavailable, log_model_call

    try:
        log_model_call(
            ModelCallLog(
                execution_run_id=UUID(ctx.run_id_str) if ctx.run_id_str else None,
                work_packet_id=ctx.packet.id,
                file_path=file_path,
                task_type=task_type,
                model_group=model_group,
                actual_model=actual_model,
                local_or_cloud="local",
                prompt_chars=prompt_chars,
                response_chars=response_chars,
                success=success,
                error=error,
            )
        )
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not log model_call: {exc}")


def _maybe_save_evaluation(
    ctx: StepContext, *, evaluation, file_path: str | None
) -> None:
    if not ctx.persist_to_db:
        return
    from assistant_core.storage import StorageUnavailable, save_evaluation

    try:
        save_evaluation(
            evaluation,
            execution_run_id=ctx.run_id_str,
            work_packet_id=str(ctx.packet.id),
            file_path=file_path,
        )
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not save evaluation: {exc}")


def _maybe_save_memory_candidate(
    ctx: StepContext, candidate: MemoryCandidate
) -> None:
    from assistant_core.storage import StorageUnavailable, save_memory_candidate

    try:
        save_memory_candidate(candidate)
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not save memory candidate: {exc}")


def _maybe_update_packet_status(ctx: StepContext, status: str) -> None:
    from assistant_core.storage import StorageUnavailable, update_work_packet_status

    try:
        update_work_packet_status(str(ctx.packet.id), status)
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not update packet status: {exc}")


def _finalize_run_row(ctx: StepContext, *, db_status: str) -> None:
    if not ctx.persist_to_db or ctx.run_id_str is None:
        return
    from assistant_core.storage import StorageUnavailable, complete_execution_run

    summary = "; ".join(ctx.result.errors[-3:]) if ctx.result.errors else None
    try:
        complete_execution_run(ctx.run_id_str, status=db_status, error_summary=summary)
    except StorageUnavailable as exc:
        ctx.result.errors.append(f"could not finalize execution_run: {exc}")


__all__ = [
    # Top-level steps (in pipeline order)
    "safety_gate",
    "initialize_run",
    "scan_sources",
    "process_sources",
    "cloud_review_gate",
    "synthesize_brief",
    "write_outputs",
    "write_obsidian",
    "generate_memory_candidates",
    "archive_processed_files",
    "finalize_run",
    # Constants
    "PRIMARY_GROUP",
    "SECONDARY_GROUP",
    "REASONER_GROUP",
    "CODER_GROUP",
    "EVAL_REQUIRED_TERMS",
    "SUPPORTED_EXTENSIONS",
]
