from __future__ import annotations

from pathlib import Path

from assistant_core.config import AssistantConfig, load_assistant_config, load_memory_config


LOCALAI_SUBDIRS = [
    "inbox/notes",
    "inbox/transcripts",
    "inbox/docs",
    "inbox/csv",
    "inbox/cloud_review",
    "output",
    "archive",
    "logs",
    "state",
    "work_packets",
]

OBSIDIAN_SUBDIRS = [
    "00_Inbox/Memory_Review",
    "01_Daily_Briefs",
    "02_Work_Packets",
    "03_Projects",
    "04_Meetings",
    "05_Decisions",
    "06_Stakeholders",
    "07_Playbooks",
    "08_Prompts",
    "09_System_Logs_Summaries",
    "99_Archive",
]


class PathSafetyError(ValueError):
    """Raised when a path escapes the configured writable roots."""


def ensure_local_folders(config: AssistantConfig | None = None) -> list[Path]:
    cfg = config or load_assistant_config()
    created: list[Path] = []
    for relative in LOCALAI_SUBDIRS:
        path = cfg.local_ai_root / relative
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    memory_cfg = load_memory_config()
    for relative in OBSIDIAN_SUBDIRS:
        path = memory_cfg.obsidian_vault_dir / relative
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created


def resolve_user_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def assert_within_roots(path: str | Path, allowed_roots: list[str | Path]) -> Path:
    resolved = resolve_user_path(path)
    roots = [resolve_user_path(root) for root in allowed_roots]
    if not any(is_relative_to(resolved, root) for root in roots):
        root_text = ", ".join(str(root) for root in roots)
        raise PathSafetyError(f"Refusing path outside allowed roots: {resolved}. Allowed roots: {root_text}")
    return resolved


def default_allowed_write_roots(config: AssistantConfig | None = None) -> list[Path]:
    cfg = config or load_assistant_config()
    return [cfg.output_dir, cfg.log_dir, cfg.work_packets_dir, cfg.archive_dir, cfg.obsidian_vault_dir]
