"""The ordered execution pipeline.

This module is the single source of truth for **what runs in what order**.

  - To add a step: write it in ``steps.py``, then add the callable to
    EXECUTION_GRAPH below in the position you want.
  - To remove a step: delete the line from EXECUTION_GRAPH (the function
    stays in steps.py until you remove it).
  - To reorder: move lines in EXECUTION_GRAPH.
  - To inspect what the pipeline does: read this file.

The runner (``runner.py``) just iterates EXECUTION_GRAPH. Steps signal
"stop iterating" by setting ``ctx.halt = True``.

EXECUTION_STEPS (below) is the documented, human-readable list of all
step names that *can* appear in a pipeline. It is for documentation and
the Streamlit Execution tab. The actual runtime order is EXECUTION_GRAPH.
"""

from __future__ import annotations

from typing import Callable

from assistant_core.execution import steps
from assistant_core.execution.context import StepContext


# Type of a pipeline step. Matches the signature of every callable in
# EXECUTION_GRAPH and lets static checkers complain when an entry doesn't fit.
PipelineStep = Callable[[StepContext], StepContext]


# -----------------------------------------------------------------------------
# THE PIPELINE.
#
# Order matters. Each entry is a callable from ``steps`` that takes a
# StepContext and returns it (with mutations).
# -----------------------------------------------------------------------------

EXECUTION_GRAPH: list[PipelineStep] = [
    steps.safety_gate,             # 1. Refuse if mode/unlock disallows local models
    steps.initialize_run,          # 2. Create execution_runs row (best-effort)
    steps.scan_sources,            # 3. Collect supported files under source_paths
    steps.process_sources,         # 4. Per-file: load -> classify -> chunk ->
                                   #    extract via local-main -> evaluate
                                   #    (sub-steps live in steps._process_one_source)
    steps.cloud_review_gate,       # 5. Scaffolded: cloud_review_gate +
                                   #    execute_claude_opus_if_authorized
    steps.synthesize_brief,        # 6. Combine extractions into one brief via local-main
    steps.write_outputs,           # 7. Write 00_STATUS.json, 01_MORNING_BRIEF.md,
                                   #    09_AUDIT_LOG.md, and _extractions/*.md
    steps.write_obsidian,          # 8. Mirror the brief into the Obsidian vault
    steps.generate_memory_candidates,  # 9. Extract candidates into Memory_Review
    steps.archive_processed_files, # 10. Scaffolded: move inputs to ~/LocalAI/archive/
    steps.finalize_run,            # 11. Close execution_runs row; update packet status
]


# -----------------------------------------------------------------------------
# Documented (descriptive) step names, including the inner sub-steps that live
# inside process_sources. This is what the panel's Execution tab displays
# and what the System Guide / Technical Reference PDFs reference.
# -----------------------------------------------------------------------------

EXECUTION_STEPS: list[str] = [
    # Top-level pipeline (matches EXECUTION_GRAPH order)
    "safety_gate",
    "initialize_run",
    "scan_sources",
    "process_sources",
    "cloud_review_gate",
    "synthesize_brief",
    "write_outputs",
    "write_obsidian",
    "generate_memory_candidates",
    "archive_processed_files",
    "finalize_run",
    # Sub-steps inside process_sources (one iteration per source file)
    "  load_file",
    "  classify_file_task",
    "  privacy_gate",
    "  chunk_content",
    "  execute_primary_local",
    "  evaluate_primary",
    "  execute_secondary_local_if_needed",
    "  reasoning_check_if_needed",
]


# -----------------------------------------------------------------------------
# Public helpers consumed by the panel and tests.
# -----------------------------------------------------------------------------

def step_names() -> list[str]:
    """Return the top-level callables' names, in pipeline order."""
    return [step.__name__ for step in EXECUTION_GRAPH]


def describe_execution_scaffold() -> dict[str, object]:
    """Used by the Streamlit Execution tab to display pipeline structure.

    Returns the runtime-truthful top-level step list plus the human-readable
    EXECUTION_STEPS (which includes the inner sub-steps).
    """
    return {
        "status": "wired",
        "note": (
            "Top-level pipeline is wired; inner per-source sub-steps run "
            "inside process_sources. cloud_review_gate and "
            "archive_processed_files are scaffolds (no-ops in v1)."
        ),
        "graph": step_names(),
        "documented_steps": EXECUTION_STEPS,
    }


__all__ = [
    "PipelineStep",
    "EXECUTION_GRAPH",
    "EXECUTION_STEPS",
    "step_names",
    "describe_execution_scaffold",
]
