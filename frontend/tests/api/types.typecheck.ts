import type {
  ApiEnvelope,
  ApiPage,
  ApiResult,
  CognitiveStateRecord,
  EvidenceRecord,
  HealthData,
  LearnerSummary,
  OpenRecord,
  RepresentationRecord,
  TrajectoryActionRequest,
  TrajectoryCreateRequest,
  TrajectoryRecord,
} from "../../lib/api/types";
import type { learnerService } from "../../lib/services/learner.service";
import type { trajectoryService } from "../../lib/services/trajectory.service";

const schemaVersion: CognitiveStateRecord["schema_version"] = "1.0";
const uncertainty: CognitiveStateRecord["uncertainty"] = {
  evidence_uncertainty: "limited",
  temporal_uncertainty: "low",
  modality_uncertainty: "high",
  inference_uncertainty: "high",
  overall_uncertainty: "high",
  uncertainty_reasons: { overall_uncertainty: ["insufficient evidence"] },
};
const page: ApiPage<EvidenceRecord> = { items: [], limit: 20, offset: 0, total: 0, has_more: false };
const health: HealthData = { status: "degraded", api_version: "1.0.0", database: "unavailable", modules: {}, timestamp: "" };
const healthEnvelope: ApiEnvelope<HealthData> = { success: true, data: health, request_id: "req" };
const create: TrajectoryCreateRequest = { target_concept_id: "c1", primary_learning_goal: "Caller-provided goal", previous_cognitive_state_id: null };
const action: TrajectoryActionRequest = { action: "pause", reason: "Need review", evidence_ids: [] };
const state: TrajectoryRecord["current_status"] = "ACTIVE";
const plan: RepresentationRecord["decision"] = {
  selected_representation: null,
  selected_action: "defer",
  delivery_status: "unavailable",
  capability_reference: null,
  decision_reason: "No executable provider is available.",
  decision_method: "rule_based",
  decision_confidence: "limited",
  confidence_scope: "decision support only",
  policy_trace: [],
  alternative_representations: [],
};
declare const learnerList: ReturnType<typeof learnerService.list>;
const learnerListContract: Promise<ApiResult<ApiPage<LearnerSummary>>> = learnerList;
declare const trajectoryHistory: ReturnType<typeof trajectoryService.history>;
const trajectoryHistoryContract: Promise<ApiResult<ApiPage<OpenRecord>>> = trajectoryHistory;

void [schemaVersion, uncertainty, page, healthEnvelope, create, action, state, plan, learnerListContract, trajectoryHistoryContract];
