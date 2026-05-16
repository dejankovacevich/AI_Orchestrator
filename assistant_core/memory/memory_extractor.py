from __future__ import annotations

from pathlib import Path

from assistant_core.schemas import MemoryCandidate


def extract_memory_candidates(output_text: str, source_path: str | Path) -> list[MemoryCandidate]:
    candidates: list[MemoryCandidate] = []
    for line in output_text.splitlines():
        stripped = line.strip("- ").strip()
        if not stripped or len(stripped) < 30:
            continue
        if any(marker in stripped.lower() for marker in ["decision:", "confirmed:", "preference:"]):
            candidates.append(
                MemoryCandidate(
                    candidate_text=stripped,
                    destination_suggestion="00_Inbox/Memory_Review",
                    confidence="medium",
                    memory_type="derived",
                    source_path=str(source_path),
                )
            )
    return candidates
