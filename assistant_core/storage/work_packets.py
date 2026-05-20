"""CRUD for the ``work_packets`` table.

Public entry points used by the CLI, the runner, and the Streamlit panel.
Each function opens a short-lived connection so callers don't share state.
"""

from __future__ import annotations

from typing import Any

from assistant_core.schemas import WorkPacket
from assistant_core.storage.connection import StorageUnavailable, _connect, _json
from assistant_core.storage.serialization import (
    deserialize_work_packet,
    serialize_work_packet,
)


def create_work_packet(packet: WorkPacket, postgres_url: str | None = None) -> WorkPacket:
    """Insert a new packet. Updates packet.structured_yaml in-place and returns it."""
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
    """Load a packet by id. Prefers the structured_yaml column when present."""
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
    """Persist all mutable columns from the supplied packet. Touches updated_at."""
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


def list_work_packets(postgres_url: str | None = None) -> list[dict[str, Any]]:
    """Return the 100 most recently created packets as dicts (for the dashboard)."""
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


def update_work_packet_status(
    work_packet_id: str,
    status: str,
    readiness_score: float | None = None,
    postgres_url: str | None = None,
) -> None:
    """Update status (and optionally readiness) without touching the YAML column."""
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
    """Return ids of packets eligible for overnight execution."""
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM work_packets "
                "WHERE status IN ('READY_FOR_OVERNIGHT', 'READY_HIGH_CONFIDENCE')"
            )
            return [str(row[0]) for row in cur.fetchall()]


__all__ = [
    "create_work_packet",
    "get_work_packet",
    "update_work_packet",
    "list_work_packets",
    "update_work_packet_status",
    "ready_work_packet_ids",
]
