"""Storage layer for the orchestrator's Postgres state.

The public API is identical to the pre-split ``assistant_core.storage`` module:
external callers continue to ``from assistant_core.storage import ...``.

Internally the responsibilities are now organized by entity:

  - connection.py        Postgres connection management + StorageUnavailable
  - serialization.py     WorkPacket <-> YAML round-trip
  - migration.py         Apply SQL migrations on a fresh DB
  - work_packets.py      CRUD for the work_packets table
  - clarification.py     CRUD for clarification_questions
  - execution_runs.py    Lifecycle of one overnight run
  - audit.py             model_calls, evaluations, artifacts, memory_candidates

Each submodule is small (~30-80 lines) and tests directly against the
public re-exports below.
"""

from __future__ import annotations

from assistant_core.storage.audit import (
    log_model_call,
    save_artifact,
    save_evaluation,
    save_memory_candidate,
)
from assistant_core.storage.clarification import (
    mark_open_questions_answered,
    save_questions,
)
from assistant_core.storage.connection import StorageUnavailable
from assistant_core.storage.execution_runs import (
    complete_execution_run,
    create_execution_run,
)
from assistant_core.storage.migration import run_migration
from assistant_core.storage.serialization import (
    deserialize_work_packet,
    serialize_work_packet,
)
from assistant_core.storage.work_packets import (
    create_work_packet,
    get_work_packet,
    list_work_packets,
    ready_work_packet_ids,
    update_work_packet,
    update_work_packet_status,
)


__all__ = [
    # connection
    "StorageUnavailable",
    # serialization
    "serialize_work_packet",
    "deserialize_work_packet",
    # migration
    "run_migration",
    # work_packets
    "create_work_packet",
    "get_work_packet",
    "update_work_packet",
    "list_work_packets",
    "update_work_packet_status",
    "ready_work_packet_ids",
    # clarification
    "save_questions",
    "mark_open_questions_answered",
    # execution_runs
    "create_execution_run",
    "complete_execution_run",
    # audit
    "log_model_call",
    "save_evaluation",
    "save_artifact",
    "save_memory_candidate",
]
