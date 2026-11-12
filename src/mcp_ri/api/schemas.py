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


class Phase9ObservationWindow(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    recent_overall_labeled_responses: int
    recent_concept_labeled_responses: int
    trend_comparison: str


class Phase9ObservationSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_interactions: int
    labelled_responses: int
    unlabelled_interactions: int
    unique_concepts_observed: int
    interactions_without_skill_mapping: int
    preserved_duplicate_interactions: int


class Phase9Performance(BaseModel):
    model_config = ConfigDict(extra="allow")

    estimated_performance: float
    recent_performance: float | None
    historical_performance: float | None
    performance_change: float | None
    performance_trend: str
    attempts: int
    correct: int
    incorrect: int
    evidence_type: str
    evidence_sufficiency: str
    estimate_confidence: str
    uncertainty_level: str
    uncertainty_interval_95: list[float] | None
    uncertainty_reason: list[str]
    potential_issues: list[str]


class Phase9ConceptState(BaseModel):
    model_config = ConfigDict(extra="allow")

    concept_id: str
    attempts: int
    correct: int
    incorrect: int
    historical_accuracy: float | None
    recent_accuracy: float | None
    smoothed_performance: float
    performance_trend: str
    performance_change: float | None
    last_observed_interaction: dict[str, Any] | None
    evidence_count: int
    evidence_sufficiency: str
    estimate_confidence: str
    uncertainty_level: str
    uncertainty_interval_95: list[float] | None
    uncertainty_reason: list[str]
    potential_issues: list[str]
    evidence_type: str


class Phase9ModelPrediction(BaseModel):
    model_config = ConfigDict(extra="allow")

    next_response_correctness: float | None
    model_name: str | None
    availability: str
    reason: str


class BehavioralStateRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"]
    learner_id: str
    state_timestamp: str | None
    observation_window: Phase9ObservationWindow
    observation_summary: Phase9ObservationSummary
    learning_performance: Phase9Performance
    concept_states: list[Phase9ConceptState]
    model_predictions: Phase9ModelPrediction
    limitations: list[str]


class EvidenceTemporal(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_timestamp: str | None
    ingestion_timestamp: str
    sequence_number: int | None
    temporal_precision: str
    timestamp_source: str | None


class EvidenceProvenance(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_dataset: str
    source_file: str | None
    source_record_id: str | None
    source_modality: str
    processing_method: str
    processing_version: str


class EvidenceProcessing(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    processing_timestamp: str
    extraction_method: str
    quality_flags: list[str]
    missing_fields: list[str]
    transformation_history: list[str]


class EvidenceUncertainty(BaseModel):
    model_config = ConfigDict(extra="allow")

    flags: list[str]
    processing_confidence: float | None
    notes: list[str]


class EvidenceAlignmentLink(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"]
    left_evidence_id: str
    right_evidence_id: str
    alignment_type: str
    absolute_delta_ms: int | None
    alignment_uncertainty: str
    uncertainty_flags: list[str]


class EvidenceGroup(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"]
    group_id: str
    learner_id: str
    session_id: str | None
    evidence_ids: list[str]
    grouping_basis: str
    modalities_present: list[str]
    modality_availability: dict[str, dict[str, Any]]
    alignment_links: list[EvidenceAlignmentLink]
    uncertainty_flags: list[str]


class EvidenceRecord(ResearchRecord):
    schema_version: Literal["1.0"]
    evidence_id: str
    session_id: str | None
    evidence_type: Literal["text", "audio", "visual", "interaction", "temporal_history"]
    temporal: EvidenceTemporal
    provenance: EvidenceProvenance
    content: dict[str, Any]
    processing: EvidenceProcessing
    uncertainty: EvidenceUncertainty
    related_evidence_ids: list[str] = Field(default_factory=list)
    duplicate_candidates: list[Any] = Field(default_factory=list)
    content_fingerprint: str
    grouping_information: list[EvidenceGroup] = Field(default_factory=list)
    alignment_links: list[EvidenceAlignmentLink] = Field(default_factory=list)
    grouping_annotations_available: bool = False


class CognitiveUncertainty(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_uncertainty: str
    temporal_uncertainty: str
    modality_uncertainty: str
    inference_uncertainty: str
    overall_uncertainty: str
    uncertainty_reasons: dict[str, list[str]]


class CognitiveStateRecord(ResearchRecord):
    schema_version: Literal["1.0"]
    cognitive_state_id: str
    generated_at: str
    state_timestamp: str | None
    state_version: int
    previous_state_id: str | None
    observation_window: dict[str, Any]
    relevant_concept_ids: list[str]
    evidence_references: list[dict[str, Any]]
    observed_evidence_summary: dict[str, Any]
    concept_estimates: list[dict[str, Any]]
    possible_difficulty_hypotheses: list[dict[str, Any]]
    uncertainty: CognitiveUncertainty
    diagnostic_recommendations: list[dict[str, Any]]
    state_change_summary: dict[str, Any]
    limitations: list[str]


class RepresentationDecision(BaseModel):
    model_config = ConfigDict(extra="allow")

    selected_representation: str | None
    selected_action: str
    delivery_status: str
    capability_reference: dict[str, Any] | None
    decision_reason: str
    decision_method: str
    decision_confidence: str
    confidence_scope: str
    policy_trace: list[dict[str, Any]]
    alternative_representations: list[dict[str, Any]]


class RepresentationRecord(ResearchRecord):
    schema_version: Literal["1.0"]
    taxonomy_version: str
    plan_id: str
    concept_id: str
    created_at: str
    plan_version: int
    previous_plan_id: str | None
    plan_kind: str
    input_references: dict[str, Any]
    teaching_context: dict[str, Any]
    concept_grounding: dict[str, Any]
    decision: RepresentationDecision
    learning_objective: dict[str, Any]
    representation_configuration: dict[str, Any]
    evaluation_strategy: list[dict[str, Any]]
    limitations: dict[str, Any]


class TrajectoryStep(BaseModel):
    model_config = ConfigDict(extra="allow")

    step_id: str
    concept_id: str
    objective: str
    status: Literal["pending", "current", "completed"]


class TrajectoryContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    previous_representation_plan_id: str | None
    previous_cognitive_state_id: str | None
    supporting_evidence_ids: list[str]
    previous_interventions: list[dict[str, Any]]
    learning_history_reference: str | None


class TrajectoryOrchestration(BaseModel):
    model_config = ConfigDict(extra="allow")

    active_diversion_id: str | None
    parent_trajectory_id: str | None
    current_depth: int
    transition_history_reference: str


class TrajectoryRecordModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"]
    trajectory_id: str
    learner_id: str
    created_at: str
    updated_at: str
    trajectory_version: int
    primary_learning_goal: str
    target_concept_id: str
    target_skill_ids: list[str]
    learning_objectives: list[str]
    prerequisites: list[str]
    expected_progression: list[TrajectoryStep]
    current_concept_id: str
    current_learning_step: str
    completed_steps: list[str]
    pending_steps: list[str]
    current_status: Literal["CREATED", "ACTIVE", "PAUSED", "DIVERTED", "RESUMING", "COMPLETED", "REPLANNED", "CANCELLED"]
    context: TrajectoryContext
    orchestration: TrajectoryOrchestration


class DiversionRecordModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    diversion_id: str
    learner_id: str
    schema_version: Literal["1.0"]
    diversion_version: int
    parent_trajectory_id: str
    context_snapshot_id: str
    diversion_concept_id: str
    diversion_reason: str
    diversion_status: Literal["ACTIVE", "RESOLVED", "CLOSED", "CANCELLED"]


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
