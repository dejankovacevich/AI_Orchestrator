"""Lifecycle of one overnight ``execution_runs`` row.

Created at the start of a run (status RUNNING), updated at the end with
the terminal status and optional error_summary.
"""

from __future__ import annotations

from assistant_core.storage.connection import _connect


def create_execution_run(
    work_packet_id: str,
    *,
    mode: str,
    status: str = "RUNNING",
    temporal_workflow_id: str | None = None,
    postgres_url: str | None = None,
) -> str:
    """Insert a new run row. Returns the UUID as a string."""
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


def complete_execution_run(
    run_id: str,
    *,
    status: str = "COMPLETED",
    error_summary: str | None = None,
    postgres_url: str | None = None,
) -> None:
    """Close out an existing run row. Sets completed_at and the final status."""
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


__all__ = ["create_execution_run", "complete_execution_run"]
