"""Apply SQL migrations against a fresh Postgres instance.

In normal operation, db/migrations/*.sql is mounted into the Postgres
container's docker-entrypoint-initdb.d, so this function is only used
for manual recovery or test setups.
"""

from __future__ import annotations

from pathlib import Path

from assistant_core.storage.connection import _connect


def run_migration(
    sql_path: str | Path = "db/migrations/001_init.sql",
    postgres_url: str | None = None,
) -> None:
    """Execute the SQL file against the configured Postgres instance."""
    path = Path(sql_path)
    with _connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()


__all__ = ["run_migration"]
