/**
 * Manually maintained transport types from shared/api-contracts/openapi.json
 * (OpenAPI 3.1, MCP-RI Backend API 1.0.0). Regenerate/review when that
 * checked-in contract changes. Open-ended artifact fields use JSON types
 * because FastAPI intentionally preserves Phase 9–13 record payloads.
 */
export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | JsonObject;
export type JsonObject = { [key: string]: JsonValue };

export interface ApiEnvelope<T> {
  success: true;
  data: T;
  request_id: string;
}

export interface ApiErrorEnvelope {
  success: false;
  error: {
    code: string;
    message: string;
    fields?: string[] | null;
  };
  timestamp: string;
  request_id: string;
}

export interface ApiPage<T> {
  items: T[];
  limit: number;
  offset: number;
  total: number;
  has_more: boolean;
}

export interface HealthData {
  status: "healthy" | "degraded";
  api_version: string;
  database: "available" | "unavailable";
  modules: Record<string, Record<string, JsonValue>>;
  timestamp: string;
}

export interface LearnerSummary {
  learner_id: string;
  available_data: string[];
}

export interface LearnerDetail {
  learner_id: string;
  available_data: string[];
  trajectory_count: number;
  source: "research_artifacts" | "application";
}

export interface CognitiveUncertainty {
  evidence_uncertainty: string;
  temporal_uncertainty: string;
  modality_uncertainty: string;
  inference_uncertainty: string;
  overall_uncertainty: string;
  uncertainty_reasons: Record<string, string[]>;
}

/** Phase 9 behavioral snapshot returned by GET /learners/{learner_id}/state. */
export interface BehavioralStateRecord {
  schema_version: "1.0";
  learner_id: string;
  state_timestamp: string | null;
  observation_window: JsonObject;
  observation_summary: JsonObject;
  learning_performance: JsonObject;
  concept_states: JsonObject[];
  model_predictions: JsonObject;
  limitations: string[];
}

/** Phase 11 cognitive estimate returned by GET /learners/{learner_id}/cognitive-state. */
export interface CognitiveStateRecord {
  learner_id: string;
  schema_version: "1.0";
  cognitive_state_id: string;
  generated_at: string;
  state_timestamp: string | null;
  state_version: number;
  previous_state_id: string | null;
  observation_window: JsonObject;
  relevant_concept_ids: string[];
  evidence_references: JsonObject[];
  observed_evidence_summary: JsonObject;
  concept_estimates: JsonObject[];
  possible_difficulty_hypotheses: JsonObject[];
  uncertainty: CognitiveUncertainty;
  diagnostic_recommendations: JsonObject[];
  state_change_summary: JsonObject;
  limitations: string[];
}

export interface EvidenceTemporal {
  event_timestamp: string | null;
  ingestion_timestamp: string;
  sequence_number: number | null;
  temporal_precision: string;
  timestamp_source: string | null;
}

export interface EvidenceProvenance {
  source_dataset: string;
  source_file: string | null;
  source_record_id: string | null;
  source_modality: string;
  processing_method: string;
  processing_version: string;
}

export interface EvidenceProcessing {
  status: string;
  processing_timestamp: string;
  extraction_method: string;
  quality_flags: string[];
  missing_fields: string[];
  transformation_history: string[];
}

export interface EvidenceUncertainty {
  flags: string[];
  processing_confidence: number | null;
  notes: string[];
}

export interface EvidenceAlignmentLink {
  schema_version: "1.0";
  left_evidence_id: string;
  right_evidence_id: string;
  alignment_type: string;
  absolute_delta_ms: number | null;
  alignment_uncertainty: string;
  uncertainty_flags: string[];
}

export interface EvidenceGroup {
  schema_version: "1.0";
  group_id: string;
  learner_id: string;
  session_id: string | null;
  evidence_ids: string[];
  grouping_basis: string;
  modalities_present: string[];
  modality_availability: Record<string, JsonObject>;
  alignment_links: EvidenceAlignmentLink[];
  uncertainty_flags: string[];
}

export interface EvidenceRecord {
  evidence_id: string;
  learner_id: string;
  schema_version: "1.0";
  session_id: string | null;
  evidence_type: "text" | "audio" | "visual" | "interaction" | "temporal_history";
  temporal: EvidenceTemporal;
  provenance: EvidenceProvenance;
  content: JsonObject;
  processing: EvidenceProcessing;
  uncertainty: EvidenceUncertainty;
  content_fingerprint: string;
  related_evidence_ids?: string[];
  duplicate_candidates?: JsonValue[];
  grouping_information?: EvidenceGroup[];
  alignment_links?: EvidenceAlignmentLink[];
  grouping_annotations_available?: boolean;
}

export interface RepresentationDecision {
  selected_representation: string | null;
  selected_action: string;
  delivery_status: string;
  capability_reference: JsonObject | null;
  decision_reason: string;
  decision_method: string;
  decision_confidence: string;
  confidence_scope: string;
  policy_trace: JsonObject[];
  alternative_representations: JsonObject[];
}

export interface RepresentationRecord {
  learner_id: string;
  schema_version: "1.0";
  taxonomy_version: string;
  plan_id: string;
  concept_id: string;
  created_at: string;
  plan_version: number;
  previous_plan_id: string | null;
  plan_kind: string;
  input_references: JsonObject;
  teaching_context: JsonObject;
  concept_grounding: JsonObject;
  decision: RepresentationDecision;
  learning_objective: JsonObject;
  representation_configuration: JsonObject;
  evaluation_strategy: JsonObject[];
  limitations: JsonObject;
}

export interface TrajectoryRecord {
  schema_version: "1.0";
  trajectory_id: string;
  learner_id: string;
  created_at: string;
  updated_at: string;
  trajectory_version: number;
  target_concept_id: string;
  primary_learning_goal: string;
  target_skill_ids: string[];
  learning_objectives: string[];
  prerequisites: string[];
  expected_progression: TrajectoryStep[];
  current_concept_id: string;
  current_learning_step: string;
  completed_steps: string[];
  pending_steps: string[];
  current_status: "CREATED" | "ACTIVE" | "PAUSED" | "DIVERTED" | "RESUMING" | "COMPLETED" | "REPLANNED" | "CANCELLED";
  context: TrajectoryContext;
  orchestration: TrajectoryOrchestration;
}

export interface TrajectoryStep {
  step_id: string;
  concept_id: string;
  objective: string;
  status: "pending" | "current" | "completed";
}

export interface TrajectoryContext {
  previous_representation_plan_id: string | null;
  previous_cognitive_state_id: string | null;
  supporting_evidence_ids: string[];
  previous_interventions: JsonObject[];
  learning_history_reference: string | null;
}

export interface TrajectoryOrchestration {
  active_diversion_id: string | null;
  parent_trajectory_id: string | null;
  current_depth: number;
  transition_history_reference: string;
}

/** Diversion and history responses are intentionally open-ended dictionaries in OpenAPI. */
export type OpenRecord = JsonObject;

export interface TrajectoryCreateRequest {
  target_concept_id: string;
  primary_learning_goal: string;
  target_skill_ids?: string[];
  learning_objectives?: string[];
  previous_representation_plan_id?: string | null;
  previous_cognitive_state_id?: string | null;
  supporting_evidence_ids?: string[];
}

export interface TrajectoryActionRequest {
  action: "activate" | "pause" | "advance_step";
  reason?: string | null;
  evidence_ids?: string[];
}

export interface ApiResult<T> {
  /** Successful 204/empty-body responses are represented explicitly as undefined. */
  data: T | undefined;
  requestId: string | null;
  status: number;
}

export interface PageQuery {
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
}
