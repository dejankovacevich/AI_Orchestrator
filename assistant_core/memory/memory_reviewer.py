from __future__ import annotations

from pathlib import Path

from assistant_core.memory.obsidian import write_memory_candidate
from assistant_core.schemas import MemoryCandidate


def queue_memory_candidates(candidates: list[MemoryCandidate]) -> list[Path]:
    return [write_memory_candidate(candidate) for candidate in candidates if candidate.confidence != "low"]
