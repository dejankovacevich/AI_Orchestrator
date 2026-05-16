from __future__ import annotations

from datetime import date
from pathlib import Path

from assistant_core.config import AssistantConfig, load_assistant_config
from assistant_core.paths import OBSIDIAN_SUBDIRS, assert_within_roots
from assistant_core.schemas import MemoryCandidate, WorkPacket


def ensure_obsidian_vault(config: AssistantConfig | None = None) -> list[Path]:
    cfg = config or load_assistant_config()
    created: list[Path] = []
    for relative in OBSIDIAN_SUBDIRS:
        path = cfg.obsidian_vault_dir / relative
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created


def write_daily_brief(content: str, config: AssistantConfig | None = None, day: date | None = None) -> Path:
    cfg = config or load_assistant_config()
    target = cfg.obsidian_vault_dir / "01_Daily_Briefs" / f"{(day or date.today()).isoformat()}.md"
    assert_within_roots(target, [cfg.obsidian_vault_dir / "01_Daily_Briefs"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def write_work_packet_note(packet: WorkPacket, config: AssistantConfig | None = None) -> Path:
    cfg = config or load_assistant_config()
    target = cfg.obsidian_vault_dir / "02_Work_Packets" / f"{packet.created_at.date()}-{packet.id}.md"
    assert_within_roots(target, [cfg.obsidian_vault_dir / "02_Work_Packets"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# {packet.title}\n\nStatus: {packet.status}\nReadiness: {packet.readiness_score}\n", encoding="utf-8")
    return target


def write_memory_candidate(candidate: MemoryCandidate, config: AssistantConfig | None = None) -> Path:
    cfg = config or load_assistant_config()
    target = cfg.obsidian_vault_dir / "00_Inbox" / "Memory_Review" / f"{candidate.created_at.date()}-{candidate.id}.md"
    assert_within_roots(target, [cfg.obsidian_vault_dir / "00_Inbox" / "Memory_Review"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"# Memory Candidate\n\n"
        f"- Type: {candidate.memory_type}\n"
        f"- Confidence: {candidate.confidence}\n"
        f"- Source: {candidate.source_path}\n"
        f"- Destination suggestion: {candidate.destination_suggestion}\n\n"
        f"{candidate.candidate_text}\n",
        encoding="utf-8",
    )
    return target
