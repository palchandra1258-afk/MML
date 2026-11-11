"""Stable version-1 HTTP request and response models."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing_extensions import Annotated


T = TypeVar("T")
Identifier = Annotated[str, StringConstraints(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")]


class Envelope(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T
    request_id: str


class ErrorDetails(BaseModel):
    code: str
    message: str
    fields: list[str] | None = None


class ErrorEnvelope(BaseModel):
    success: Literal[False] = False
    error: ErrorDetails
    timestamp: str
    request_id: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    limit: int
    offset: int
    total: int
    has_more: bool


class LearnerSummary(BaseModel):
    learner_id: str
    available_data: list[str]


class LearnerDetail(BaseModel):
    learner_id: str
    available_data: list[str]
    trajectory_count: int
    source: Literal["research_artifacts", "application"]


class HealthData(BaseModel):
    status: Literal["healthy", "degraded"]
    api_version: str
    database: Literal["available", "unavailable"]
    modules: dict[str, dict[str, Any]]
    timestamp: str


class ResearchRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    learner_id: str
    schema_version: str | None = None


class EvidenceRecord(ResearchRecord):
    evidence_id: str
    evidence_type: str
    temporal: dict[str, Any]
    provenance: dict[str, Any]
    content: dict[str, Any]
    processing: dict[str, Any]
    uncertainty: dict[str, Any]
    related_evidence_ids: list[str] = Field(default_factory=list)
    duplicate_candidates: list[str] = Field(default_factory=list)


class CognitiveStateRecord(ResearchRecord):
    cognitive_state_id: str
    generated_at: str
    state_version: int
    uncertainty: dict[str, Any] | None = None


class RepresentationRecord(ResearchRecord):
    plan_id: str
    concept_id: str
    created_at: str
    plan_version: int
    selected_representation: str | None = None
    selected_action: str | None = None


class TrajectoryRecordModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    trajectory_id: str
    learner_id: str
    target_concept_id: str
    primary_learning_goal: str
    current_status: str
    current_concept_id: str
    current_learning_step: str
    completed_steps: list[str]
    pending_steps: list[str]
    expected_progression: list[dict[str, Any]]
    context: dict[str, Any]
    orchestration: dict[str, Any]
    trajectory_version: int


class DiversionRecordModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    diversion_id: str
    learner_id: str
    parent_trajectory_id: str
    diversion_version: int
    status: str


class TrajectoryCreateRequest(BaseModel):
    target_concept_id: Identifier
    primary_learning_goal: str = Field(min_length=1, max_length=3000)
    target_skill_ids: list[Identifier] = Field(default_factory=list, max_length=100)
    learning_objectives: list[str] = Field(default_factory=list, max_length=50)
    previous_representation_plan_id: Identifier | None = None
    previous_cognitive_state_id: Identifier | None = None
    supporting_evidence_ids: list[Identifier] = Field(default_factory=list, max_length=500)


class TrajectoryActionRequest(BaseModel):
    action: Literal["activate", "pause", "advance_step"]
    reason: str | None = Field(default=None, max_length=1000)
    evidence_ids: list[Identifier] = Field(default_factory=list, max_length=500)


class ArtifactIndexData(BaseModel):
    indexed: dict[str, dict[str, Any]]


Envelope.model_rebuild()
Page.model_rebuild()
