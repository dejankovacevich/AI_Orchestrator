"""CRUD for the ``clarification_questions`` table.

Question rounds accumulate across rescores; old questions stay (marked
answered=true when an answers file is submitted) so the audit trail is intact.
"""

from __future__ import annotations

from assistant_core.schemas import ClarificationQuestion
from assistant_core.storage.connection import _connect


def save_questions(
    questions: list[ClarificationQuestion],
    postgres_url: str | None = None,
) -> None:
    """Insert a list of questions in one transaction. No-op when empty."""
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


def mark_open_questions_answered(
    work_packet_id: str,
    answer: str,
    postgres_url: str | None = None,
) -> None:
    """Flip all unanswered questions for the packet to answered with the same text."""
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


__all__ = ["save_questions", "mark_open_questions_answered"]
