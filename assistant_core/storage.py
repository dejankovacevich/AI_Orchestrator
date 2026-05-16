from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from assistant_core.config import load_assistant_config
from assistant_core.schemas import Artifact, ClarificationQuestion, EvaluationResult, MemoryCandidate, ModelCallLog, WorkPacket


class StorageUnavailable(RuntimeError):
    """Raised when Postgres is unavailable or dependencies are missing."""


def serialize_work_packet(packet: WorkPacket) -> str:
    return yaml.safe_dump(packet.model_dump(mode="json"), sort_keys=False)


def deserialize_work_packet(structured_yaml: str) -> WorkPacket:
    return WorkPacket.model_validate(yaml.safe_load(structured_yaml) or {})


def _connect(postgres_url: str | None = None):
    try:
        import psycopg
    except Exception as exc:  # pragma: no cover - depends on optional install
        raise StorageUnavailable("psycopg is not installed. Run bash scripts/install_core.sh.") from exc
    url = postgres_url or load_assistant_config().postgres_url
    try:
        return psycopg.connect(url)
    except Exception as exc:  # pragma: no cover - depends on local service
        raise StorageUnavailable(f"Postgres unavailable at {url}. Start services before using database-backed commands.") from exc


def run_migration(sql_path: str | Path = "db/migrations/001_init.sql", postgres_url: str | None = None) -> None:
    path = Path(sql_path)
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()


def create_work_packet(packet: WorkPacket, postgres_url: str | None = None) -> WorkPacket:
    packet.structured_yaml = serialize_work_packet(packet)
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO work_packets
                (id, title, objective, status, readiness_score, high_stakes, cloud_policy,
                 source_policy, output_policy, created_at, updated_at, raw_user_request, structured_yaml)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    packet.id,
                    packet.title,
                    packet.objective,
                    packet.status,
                    packet.readiness_score,
                    packet.high_stakes,
                    _json(packet.cloud_policy),
                    _json(packet.source_policy),
                    _json(packet.output_policy),
                    packet.created_at,
                    packet.updated_at,
                    packet.raw_user_request,
                    packet.structured_yaml,
                ),
            )
        conn.commit()
    return packet


def get_work_packet(work_packet_id: str, postgres_url: str | None = None) -> WorkPacket:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, objective, status, readiness_score, high_stakes, cloud_policy,
                       source_policy, output_policy, created_at, updated_at, raw_user_request, structured_yaml
                FROM work_packets
                WHERE id = %s
                """,
                (work_packet_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise StorageUnavailable(f"Work packet not found: {work_packet_id}")
            if row[12]:
                return deserialize_work_packet(row[12])
            return WorkPacket(
                id=row[0],
                title=row[1],
                objective=row[2],
                status=row[3],
                readiness_score=float(row[4]) if row[4] is not None else None,
                high_stakes=row[5],
                cloud_policy=row[6] or {},
                source_policy=row[7] or {},
                output_policy=row[8] or {},
                created_at=row[9],
                updated_at=row[10],
                raw_user_request=row[11],
            )


def update_work_packet(packet: WorkPacket, postgres_url: str | None = None) -> None:
    packet.structured_yaml = serialize_work_packet(packet)
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE work_packets
                SET title = %s,
                    objective = %s,
                    status = %s,
                    readiness_score = %s,
                    high_stakes = %s,
                    cloud_policy = %s::jsonb,
                    source_policy = %s::jsonb,
                    output_policy = %s::jsonb,
                    updated_at = now(),
                    raw_user_request = %s,
                    structured_yaml = %s
                WHERE id = %s
                """,
                (
                    packet.title,
                    packet.objective,
                    packet.status,
                    packet.readiness_score,
                    packet.high_stakes,
                    _json(packet.cloud_policy),
                    _json(packet.source_policy),
                    _json(packet.output_policy),
                    packet.raw_user_request,
                    packet.structured_yaml,
                    packet.id,
                ),
            )
        conn.commit()


def save_questions(questions: list[ClarificationQuestion], postgres_url: str | None = None) -> None:
    if not questions:
        return
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            for question in questions:
                cur.execute(
                    """
                    INSERT INTO clarification_questions
                    (id, work_packet_id, round_number, category, question, priority, blocking, answered, answer, created_at, answered_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        question.id,
                        question.work_packet_id,
                        question.round_number,
                        question.category,
                        question.question,
                        question.priority,
                        question.blocking,
                        question.answered,
                        question.answer,
                        question.created_at,
                        question.answered_at,
                    ),
                )
        conn.commit()


def mark_open_questions_answered(work_packet_id: str, answer: str, postgres_url: str | None = None) -> None:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE clarification_questions
                SET answered = true, answer = %s, answered_at = now()
                WHERE work_packet_id = %s AND answered = false
                """,
                (answer, work_packet_id),
            )
        conn.commit()


def list_work_packets(postgres_url: str | None = None) -> list[dict[str, Any]]:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, status, readiness_score, high_stakes, created_at, updated_at
                FROM work_packets
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]


def update_work_packet_status(work_packet_id: str, status: str, readiness_score: float | None = None, postgres_url: str | None = None) -> None:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE work_packets
                SET status = %s, readiness_score = COALESCE(%s, readiness_score), updated_at = now()
                WHERE id = %s
                """,
                (status, readiness_score, work_packet_id),
            )
        conn.commit()


def ready_work_packet_ids(postgres_url: str | None = None) -> list[str]:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM work_packets WHERE status IN ('READY_FOR_OVERNIGHT', 'READY_HIGH_CONFIDENCE')")
            return [str(row[0]) for row in cur.fetchall()]


def create_execution_run(work_packet_id: str, *, mode: str, status: str = "RUNNING", temporal_workflow_id: str | None = None, postgres_url: str | None = None) -> str:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO execution_runs (work_packet_id, temporal_workflow_id, status, mode, started_at)
                VALUES (%s, %s, %s, %s, now())
                RETURNING id
                """,
                (work_packet_id, temporal_workflow_id, status, mode),
            )
            run_id = str(cur.fetchone()[0])
        conn.commit()
    return run_id


def complete_execution_run(run_id: str, *, status: str = "COMPLETED", error_summary: str | None = None, postgres_url: str | None = None) -> None:
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE execution_runs
                SET status = %s, completed_at = now(), error_summary = %s
                WHERE id = %s
                """,
                (status, error_summary, run_id),
            )
        conn.commit()


def log_model_call(call: ModelCallLog, postgres_url: str | None = None) -> None:
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


def save_evaluation(evaluation: EvaluationResult, *, execution_run_id: str | None, work_packet_id: str | None, file_path: str | None = None, postgres_url: str | None = None) -> None:
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


def save_memory_candidate(candidate: MemoryCandidate, postgres_url: str | None = None) -> None:
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


def _json(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value or {})
