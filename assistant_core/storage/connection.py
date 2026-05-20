"""Postgres connection helper and the shared exception type.

Every other module in this package uses ``_connect()`` to get a live
``psycopg`` connection and ``_json()`` to safely serialize dicts into a
JSONB-compatible string.
"""

from __future__ import annotations

import json
from typing import Any

from assistant_core.config import load_assistant_config


class StorageUnavailable(RuntimeError):
    """Raised when Postgres is unavailable or psycopg is not installed.

    Callers should catch this to degrade gracefully (e.g. the execution
    runner writes filesystem artifacts even when Postgres is offline).
    """


def _connect(postgres_url: str | None = None):
    """Open a new Postgres connection. Returns a psycopg.Connection.

    Use as ``with _connect() as conn: ...``. Raises StorageUnavailable
    when psycopg is missing or the DB is unreachable.
    """
    try:
        import psycopg
    except Exception as exc:  # pragma: no cover - depends on optional install
        raise StorageUnavailable(
            "psycopg is not installed. Run bash scripts/install_core.sh."
        ) from exc
    url = postgres_url or load_assistant_config().postgres_url
    try:
        return psycopg.connect(url)
    except Exception as exc:  # pragma: no cover - depends on local service
        raise StorageUnavailable(
            f"Postgres unavailable at {url}. "
            "Start services before using database-backed commands."
        ) from exc


def _json(value: dict[str, Any]) -> str:
    """Serialize a dict as JSON for a JSONB column. None becomes '{}'."""
    return json.dumps(value or {})


__all__ = ["StorageUnavailable", "_connect", "_json"]
