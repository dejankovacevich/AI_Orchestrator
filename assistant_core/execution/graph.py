from __future__ import annotations


EXECUTION_STEPS = [
    "load_ready_work_packets",
    "scan_sources",
    "load_file",
    "classify_file_task",
    "privacy_gate",
    "chunk_content",
    "execute_primary_local",
    "evaluate_primary",
    "execute_secondary_local_if_needed",
    "reasoning_check_if_needed",
    "cloud_review_gate",
    "execute_claude_opus_if_authorized",
    "write_outputs",
    "generate_memory_candidates",
    "write_obsidian_outputs",
    "write_status",
    "archive_processed_files",
    "finish_run",
]


def describe_execution_scaffold() -> dict[str, object]:
    return {
        "status": "scaffolded",
        "note": "Full LangGraph execution will be wired in v2; v1 enforces readiness and safety gates.",
        "steps": EXECUTION_STEPS,
    }
