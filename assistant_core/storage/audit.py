"""Audit-trail writes: model_calls, evaluations, artifacts, memory_candidates.

These tables capture the per-run, per-file, per-model detail that lets you
reconstruct what happened during an overnight execution. All inserts are
append-only; nothing here updates or deletes.
"""

from __future__ import annotations

from assistant_core.schemas import (
    Artifact,
    EvaluationResult,
    MemoryCandidate,
    ModelCallLog,
)
from assistant_core.storage.connection import _connect


def log_model_call(call: ModelCallLog, postgres_url: str | None = None) -> None:
    """Insert one row into model_calls. One row per inference attempt."""
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO model_calls
                (execution_run_id, work_packet_id, file_path, task_type, model_group, actual_model,
                 local_or_cloud, prompt_chars, response_chars, success, error, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    call.execution_run_id,
                    call.work_packet_id,
                    call.file_path,
                    call.task_type,
                    call.model_group,
                    call.actual_model,
                    call.local_or_cloud,
                    call.prompt_chars,
                    call.response_chars,
                    call.success,
                    call.error,
                    call.created_at,
                ),
            )
        conn.commit()


def save_evaluation(
    evaluation: EvaluationResult,
    *,
    execution_run_id: str | None,
    work_packet_id: str | None,
    file_path: str | None = None,
    postgres_url: str | None = None,
) -> None:
    """Insert one row into evaluations. One row per evaluator pass."""
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO evaluations
                (execution_run_id, work_packet_id, file_path, quality_score, grounding_score,
                 completeness_score, actionability_score, contradiction_score, hallucination_risk,
                 needs_retry, recommended_next_step, reason, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                """,
                (
                    execution_run_id,
                    work_packet_id,
                    file_path,
                    evaluation.quality_score,
                    evaluation.grounding_score,
                    evaluation.completeness_score,
                    evaluation.actionability_score,
                    evaluation.contradiction_score,
                    evaluation.hallucination_risk,
                    evaluation.needs_retry,
                    evaluation.recommended_next_step,
                    evaluation.reason,
                ),
            )
        conn.commit()


def save_artifact(artifact: Artifact, postgres_url: str | None = None) -> None:
    """Insert one row into artifacts. One row per file the runner writes."""
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO artifacts
                (id, execution_run_id, work_packet_id, artifact_type, file_path, obsidian_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    artifact.id,
                    artifact.execution_run_id,
                    artifact.work_packet_id,
                    artifact.artifact_type,
                    str(artifact.file_path),
                    str(artifact.obsidian_path) if artifact.obsidian_path else None,
                    artifact.created_at,
                ),
            )
        conn.commit()


def save_memory_candidate(
    candidate: MemoryCandidate,
    postgres_url: str | None = None,
) -> None:
    """Insert one row into memory_candidates. Reviewer flips `approved` later."""
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memory_candidates
                (id, source_artifact_id, candidate_text, destination_suggestion, confidence,
                 memory_type, approved, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    candidate.id,
                    candidate.source_artifact_id,
                    candidate.candidate_text,
                    candidate.destination_suggestion,
                    candidate.confidence,
                    candidate.memory_type,
                    candidate.approved,
                    candidate.created_at,
                ),
            )
        conn.commit()


__all__ = [
    "log_model_call",
    "save_evaluation",
    "save_artifact",
    "save_memory_candidate",
]
