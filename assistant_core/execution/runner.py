"""Thin orchestrator over the EXECUTION_GRAPH defined in ``execution/graph.py``.

This file is intentionally small. All real work happens in
``execution/steps.py``; ordering happens in ``execution/graph.py``. The
runner's only jobs are:

  1. Resolve the input (work_packet_id from Postgres, or an in-memory packet).
  2. Build a StepContext.
  3. Iterate the steps in EXECUTION_GRAPH, halting on ``ctx.halt``.
  4. Return the populated ExecutionResult.

Adding a step? Edit ``execution/graph.py``. You should not need to touch this
file unless you are changing how the graph itself runs (logging cadence,
new context fields, etc.).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from assistant_core.config import AssistantConfig, load_assistant_config
from assistant_core.execution.context import LLMBackend, StepContext
from assistant_core.execution.graph import EXECUTION_GRAPH
from assistant_core.execution.steps import (  # re-exported for backward compatibility
    PRIMARY_GROUP,
    SECONDARY_GROUP,
)
from assistant_core.llm import ollama_admin
from assistant_core.schemas import ExecutionResult, WorkPacket


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default backend (resolved at call time so tests can inject their own)
# ---------------------------------------------------------------------------

def _default_backend(
    model_group: str, prompt: str, mode: str, manual_override: bool
) -> str:
    """Resolve the group to an Ollama tag and call quick_prompt with the safety gate.

    All real local model calls flow through this single function so the
    ``assert_model_group_allowed`` check happens in exactly one place.
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
    work_packet_id: Optional[str] = None,
    *,
    packet: Optional[WorkPacket] = None,
    mode: str = "DAY_MODE",
    manual_override: bool = False,
    backend: Optional[LLMBackend] = None,
    cfg: Optional[AssistantConfig] = None,
    day: Optional[date] = None,
    persist_to_db: bool = True,
) -> ExecutionResult:
    """Run the execution pipeline for one work packet.

    Provide either ``work_packet_id`` (loaded from Postgres) or ``packet``
    (in-memory; useful for tests and direct CLI use without DB).

    The pipeline runs every step in EXECUTION_GRAPH in order, stopping when
    a step sets ``ctx.halt = True`` (safety gate refusal, no sources, etc.)
    or when the graph is exhausted.
    """
    cfg = cfg or load_assistant_config()
    backend = backend or _default_backend
    target_day = day or date.today()

    if packet is None:
        if work_packet_id is None:
            raise ValueError("Either packet or work_packet_id must be provided")
        packet = _load_packet_or_raise(work_packet_id)

    result = ExecutionResult(work_packet_id=packet.id, mode=mode)
    ctx = StepContext(
        packet=packet,
        cfg=cfg,
        backend=backend,
        mode=mode,
        manual_override=manual_override,
        day=target_day,
        persist_to_db=persist_to_db,
        result=result,
    )

    for step in EXECUTION_GRAPH:
        if ctx.halt:
            logger.debug("pipeline halted before %s", step.__name__)
            break
        logger.debug("executing step: %s", step.__name__)
        step(ctx)

    return ctx.result


def run_all_ready_packets(
    *,
    mode: str = "NIGHT_MODE",
    manual_override: bool = False,
    backend: Optional[LLMBackend] = None,
    cfg: Optional[AssistantConfig] = None,
    day: Optional[date] = None,
) -> list[ExecutionResult]:
    """Run the pipeline for every packet currently in a READY_* status.

    Used by the overnight runner and the Temporal workflow's activity body.
    Returns one ExecutionResult per packet. If no READY packets exist, returns
    a single empty ExecutionResult with status NO_PACKETS.
    """
    cfg = cfg or load_assistant_config()
    packet_ids = _maybe_load_ready_packet_ids()
    if not packet_ids:
        from uuid import UUID

        empty = ExecutionResult(
            work_packet_id=UUID("00000000-0000-0000-0000-000000000000"),
            status="NO_PACKETS",
        )
        empty.errors.append(
            "No READY_FOR_OVERNIGHT or READY_HIGH_CONFIDENCE packets found."
        )
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
# Storage glue (private)
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


__all__ = [
    "PRIMARY_GROUP",
    "SECONDARY_GROUP",
    "run_execution_for_packet",
    "run_all_ready_packets",
]
