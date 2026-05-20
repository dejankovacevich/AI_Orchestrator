"""StepContext: the mutable state object threaded through every execution step.

Each step in ``execution/graph.py`` is a callable ``StepContext -> StepContext``.
The context accumulates state as the pipeline runs. A step that needs to halt
the pipeline sets ``ctx.halt = True``; the runner stops the loop on the next
iteration.

Keeping the context narrow and documented matters. New fields should be added
here (not bolted onto random steps) so the data shape stays auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

from assistant_core.config import AssistantConfig
from assistant_core.schemas import ExecutionResult, WorkPacket


# Signature of a "backend": something that takes (model_group, prompt, mode,
# manual_override) and returns the model's text response. Lets tests swap in
# a fake without touching Ollama.
LLMBackend = Callable[[str, str, str, bool], str]


@dataclass
class StepContext:
    """All state needed by execution steps.

    Fields are grouped by lifecycle:
      - Inputs: set once at runner entry and not mutated
      - Result: the ExecutionResult being built up
      - Pipeline state: written by one step, read by subsequent steps
      - Control: ``halt`` short-circuits the remaining steps
    """

    # -------- Inputs (set by runner; immutable from steps' perspective) ----
    packet: WorkPacket
    cfg: AssistantConfig
    backend: LLMBackend
    mode: str = "DAY_MODE"
    manual_override: bool = False
    day: date = field(default_factory=date.today)
    persist_to_db: bool = True

    # -------- Result -------------------------------------------------------
    # The ExecutionResult to return. Steps mutate this directly.
    result: ExecutionResult | None = None

    # -------- Pipeline state ----------------------------------------------
    run_id_str: str | None = None
    source_files: list[str] = field(default_factory=list)
    extractions: list[tuple[str, str]] = field(default_factory=list)  # (path, markdown)
    brief_md: str = ""
    output_dir: Path | None = None

    # -------- Control -----------------------------------------------------
    halt: bool = False
    """When True, the runner stops iterating remaining steps."""


__all__ = ["LLMBackend", "StepContext"]
