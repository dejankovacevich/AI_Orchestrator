from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


WorkPacketStatus = Literal[
    "DRAFT",
    "UNDERDEFINED",
    "NEEDS_CLARIFICATION",
    "READY_FOR_OVERNIGHT",
    "READY_HIGH_CONFIDENCE",
    "PAUSED",
    "RESUME_REQUESTED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
]


# What kind of work a packet represents. The runner picks the extract +
# synthesize prompt and the output filename from this. To add a new type:
#   1. Add the literal here.
#   2. Add templates in execution/prompts.py (EXTRACT_TEMPLATES / SYNTHESIZE_TEMPLATES).
#   3. Add an entry in execution/steps.py::TASK_OUTPUT_FILENAMES.
TaskType = Literal[
    "morning_brief",
    "code_review",
    "test_generation",
    "doc_generation",
    "decision_capture",
    "risk_scan",
]


class ExecutionPlan(BaseModel):
    summary: str = ""
    steps: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)


class WorkPacket(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    objective: str | None = None
    status: WorkPacketStatus = "DRAFT"
    task_type: TaskType = "morning_brief"
    grounding_required: bool = False
    readiness_score: float | None = None
    high_stakes: bool = False
    cloud_policy: dict[str, Any] = Field(default_factory=dict)
    source_policy: dict[str, Any] = Field(default_factory=dict)
    output_policy: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    raw_user_request: str | None = None
    structured_yaml: str | None = None
    desired_outputs: list[str] = Field(default_factory=list)
    source_paths: list[str] = Field(default_factory=list)
    audience: str | None = None
    quality_threshold: str | None = None
    assumption_policy: str | None = None
    escalation_policy: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    execution_plan: ExecutionPlan = Field(default_factory=ExecutionPlan)


class ClarificationQuestion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    work_packet_id: UUID | None = None
    round_number: int = 1
    category: str
    question: str
    priority: int = 1
    blocking: bool = True
    answered: bool = False
    answer: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    answered_at: datetime | None = None


class ReadinessScore(BaseModel):
    score: float
    status: WorkPacketStatus
    dimension_scores: dict[str, float]
    reasons: dict[str, str]
    blocking_gaps: list[str] = Field(default_factory=list)
    non_blocking_gaps: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    pass_: bool = Field(alias="pass")
    quality_score: float = 0.0
    grounding_score: float = 0.0
    completeness_score: float = 0.0
    actionability_score: float = 0.0
    contradiction_score: float = 0.0
    hallucination_risk: Literal["low", "medium", "high"] = "high"
    missing_information: list[str] = Field(default_factory=list)
    needs_retry: bool = True
    recommended_next_step: Literal[
        "pass",
        "retry_local_secondary",
        "reasoning_check",
        "cloud_review",
        "human_review",
    ] = "human_review"
    reason: str = ""


class ModelCallLog(BaseModel):
    execution_run_id: UUID | None = None
    work_packet_id: UUID | None = None
    file_path: str | None = None
    task_type: str
    model_group: str
    actual_model: str | None = None
    local_or_cloud: Literal["local", "cloud"]
    prompt_chars: int = 0
    response_chars: int = 0
    success: bool = False
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Artifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    execution_run_id: UUID | None = None
    work_packet_id: UUID | None = None
    artifact_type: str
    file_path: Path
    obsidian_path: Path | None = None
    created_at: datetime = Field(default_factory=utc_now)


class MemoryCandidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_artifact_id: UUID | None = None
    candidate_text: str
    destination_suggestion: str
    confidence: Literal["low", "medium", "high"]
    memory_type: Literal["confirmed", "derived", "inferred"]
    approved: bool = False
    source_path: str
    created_at: datetime = Field(default_factory=utc_now)


ExecutionStatus = Literal[
    "STARTED",
    "NO_SOURCES",
    "NO_PACKETS",
    "BLOCKED_BY_SAFETY",
    "COMPLETED",
    "PARTIAL_FAILURE",
    "FAILED",
]


class FileExecutionRecord(BaseModel):
    """Per-source-file outcome from one execution run."""

    file_path: str
    classified_as: str = "general"
    primary_model_group: str = "local-main"
    primary_model_tag: str | None = None
    chunks_processed: int = 0
    bytes_in: int = 0
    chars_out: int = 0
    evaluation_passed: bool = False
    retry_attempted: bool = False
    retry_succeeded: bool = False
    secondary_model_group: str | None = None
    secondary_model_tag: str | None = None
    secondary_chars_out: int = 0
    needs_cloud_review: bool = False
    escalated_to_cloud: bool = False
    cloud_response_chars: int = 0
    error: str | None = None


class CloudCandidate(BaseModel):
    """One row in the cloud review catalog (rendered to 08_CLOUD_REVIEW_CANDIDATES.md).

    A candidate is a per-file decision: local extraction failed both primary
    and secondary, so the file could benefit from cloud (Claude) review. The
    candidate captures whether the safety + budget gates allowed escalation,
    and whether we actually called cloud.
    """

    file_path: str
    reason: str
    primary_model_group: str = "local-main"
    secondary_model_group: str | None = None
    gate_passed: bool = False
    gate_block_reason: str | None = None
    escalated: bool = False
    cloud_response_chars: int = 0
    estimated_cost_usd: float | None = None


class ExecutionResult(BaseModel):
    """Summary returned by run_execution_for_packet."""

    work_packet_id: UUID
    execution_run_id: UUID | None = None
    status: ExecutionStatus = "STARTED"
    mode: str = "DAY_MODE"
    output_dir: str | None = None
    obsidian_brief_path: str | None = None
    files_processed: int = 0
    files_failed: int = 0
    model_calls: int = 0
    artifacts_written: int = 0
    memory_candidates: int = 0
    cloud_candidates_logged: int = 0
    cloud_calls_made: int = 0
    file_records: list[FileExecutionRecord] = Field(default_factory=list)
    cloud_candidates: list[CloudCandidate] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
