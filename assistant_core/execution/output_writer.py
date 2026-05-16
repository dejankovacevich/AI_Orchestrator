from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from assistant_core.config import AssistantConfig, load_assistant_config
from assistant_core.paths import assert_within_roots
from assistant_core.schemas import WorkPacket


STANDARD_FILES = {
    "01_MORNING_BRIEF.md": "# Morning Brief\n\nScaffolded v1 output. Execution graph not yet run.\n",
    "02_TODAY_PRIORITIES.md": "# Today Priorities\n\nNo execution results yet.\n",
    "03_ACTIONS_BY_PERSON.md": "# Actions By Person\n\nNo execution results yet.\n",
    "04_DECISIONS_NEEDED.md": "# Decisions Needed\n\nNo execution results yet.\n",
    "05_RISKS_AND_BLOCKERS.md": "# Risks And Blockers\n\nNo execution results yet.\n",
    "06_DRAFT_MESSAGES.md": "# Draft Messages\n\nNo external sends are allowed in v1.\n",
    "07_MEETING_PREP.md": "# Meeting Prep\n\nNo execution results yet.\n",
    "08_CLOUD_REVIEW_CANDIDATES.md": "# Cloud Review Candidates\n\nCloud fallback is disabled by default.\n",
    "09_AUDIT_LOG.md": "# Audit Log\n\nExecution graph scaffold created this run folder.\n",
}


def dated_output_dir(config: AssistantConfig | None = None, day: date | None = None) -> Path:
    cfg = config or load_assistant_config()
    target = cfg.output_dir / (day or date.today()).isoformat()
    assert_within_roots(target, [cfg.output_dir])
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_status(output_dir: Path, status: dict[str, Any]) -> Path:
    path = output_dir / "00_STATUS.json"
    path.write_text(json.dumps(status, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def write_standard_output_files(packet: WorkPacket, config: AssistantConfig | None = None) -> list[Path]:
    cfg = config or load_assistant_config()
    output_dir = dated_output_dir(cfg)
    status_path = write_status(
        output_dir,
        {
            "work_packet_id": str(packet.id),
            "title": packet.title,
            "status": "SCAFFOLDED_OUTPUTS_ONLY",
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    written = [status_path]
    for filename, content in STANDARD_FILES.items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def write_obsidian_work_packet(packet: WorkPacket, config: AssistantConfig | None = None) -> Path:
    cfg = config or load_assistant_config()
    target = cfg.obsidian_vault_dir / "02_Work_Packets" / f"{packet.created_at.date()}-{packet.id}.md"
    assert_within_roots(target, [cfg.obsidian_vault_dir / "02_Work_Packets"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"# {packet.title}\n\n"
        f"- Status: {packet.status}\n"
        f"- Readiness: {packet.readiness_score}\n"
        f"- Cloud allowed: {packet.cloud_policy.get('allowed', False)}\n\n"
        f"## Objective\n\n{packet.objective or 'Unclear'}\n",
        encoding="utf-8",
    )
    return target
