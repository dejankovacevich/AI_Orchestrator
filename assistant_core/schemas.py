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
