from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SelfConsistencyConfig(BaseModel):
    enabled: bool = False
    samples: int = 3
    merge_strategy: str = "majority_section"


class AssistantConfig(BaseModel):
    local_ai_root: Path
    inbox_dir: Path
    output_dir: Path
    archive_dir: Path
    log_dir: Path
    work_packets_dir: Path
    obsidian_vault_dir: Path
    ollama_base_url: str
    litellm_base_url: str
    temporal_address: str
    postgres_url: str
    day_mode_start: str
    night_mode_start: str
    night_mode_end: str
    clarification_required: bool = True
    minimum_readiness_for_overnight: float = 0.85
    minimum_readiness_for_high_stakes: float = 0.90
    minimum_readiness_for_cloud_enabled: float = 0.90
    max_clarification_questions_per_round: int = 7
    allow_execution_with_non_blocking_gaps: bool = True
    block_execution_if_cloud_policy_unclear: bool = True
    block_execution_if_sources_unclear: bool = True
    block_execution_if_output_unclear: bool = True
    cloud_fallback_enabled: bool = False
    cloud_fallback_policy: str = "explicit_only"
    daily_cloud_budget_usd: float = 5.0
    archive_processed_files: bool = True
    no_original_file_modification: bool = True
    no_email_sending: bool = True
    no_external_api_writes: bool = True
    quality_threshold_pass: float = 0.80
    quality_threshold_retry: float = 0.65
    max_local_attempts: int = 2
    max_chars_per_chunk: int = 12000
    temperature: float = 0.2
    top_p: float = 0.9
    self_consistency: SelfConsistencyConfig = Field(default_factory=SelfConsistencyConfig)


class MemoryConfig(BaseModel):
    obsidian_enabled: bool = True
    obsidian_vault_dir: Path
    write_daily_briefs_to_obsidian: bool = True
    write_work_packets_to_obsidian: bool = True
    write_memory_candidates_to_review_queue: bool = True
    allow_direct_existing_note_updates: bool = False
    vector_store: str = "chroma"
    vector_store_dir: Path
    embed_selected_outputs: bool = True
    embed_obsidian_vault: bool = True
    memory_policy: dict[str, Any] = Field(default_factory=dict)


def _expand_path(value: Any) -> Any:
    if isinstance(value, str) and (value.startswith("~/") or value == "~"):
        return Path(value).expanduser()
    if isinstance(value, dict):
        return {key: _expand_path(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_expand_path(item) for item in value]
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _expand_path(data)


def load_assistant_config(path: Path | None = None) -> AssistantConfig:
    config_path = path or PROJECT_ROOT / "config" / "assistant.yaml"
    return AssistantConfig.model_validate(load_yaml(config_path))


def load_memory_config(path: Path | None = None) -> MemoryConfig:
    config_path = path or PROJECT_ROOT / "config" / "memory.yaml"
    return MemoryConfig.model_validate(load_yaml(config_path))


def load_models(path: Path | None = None) -> dict[str, str]:
    config_path = path or PROJECT_ROOT / "config" / "models.yaml"
    return load_yaml(config_path)
