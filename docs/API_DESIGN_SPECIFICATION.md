# Phase 14 API Design Specification

Base URL for local development: `http://127.0.0.1:8000/api/v1`. The live contract is generated from the FastAPI application at [`shared/api-contracts/openapi.json`](../shared/api-contracts/openapi.json). Interactive docs are available at `/api/v1/docs`.

Every successful response has `success: true`, a typed `data` field, and a `request_id`. Page objects use `items`, `limit`, `offset`, `total`, and `has_more`. Every error uses the common error envelope described in [ERROR_FORMAT.md](../shared/api-contracts/ERROR_FORMAT.md).

## Read endpoints

| Method and path | Query | Result |
|---|---|---|
| `GET /health` | — | Application/API version, database, artifact/module readiness and UTC timestamp. `degraded` is expected until all configured artifacts are indexed. |
| `GET /learners` | `limit` 1–100 (default 20), `offset` (default 0) | Learner IDs present in indexed research artifacts or application records; available data names are explicit. |
| `GET /learners/{learner_id}` | — | Data availability and durable trajectory count. Unknown IDs return 404. |
| `GET /learners/{learner_id}/state` | — | Existing Phase 9 behavioral snapshot, with its uncertainty and limitations. |
| `GET /learners/{learner_id}/cognitive-state` | — | Latest Phase 11 estimate ordered by source `generated_at`; this is provisional, not a diagnosis. |
| `GET /learners/{learner_id}/evidence` | `limit`, `offset`, optional `evidence_type` | Phase 10 evidence records with provenance, missingness, uncertainty, group information and available alignment links. |
| `GET /learners/{learner_id}/evidence/{evidence_id}` | — | One evidence record, constrained to the requested learner. |
| `GET /learners/{learner_id}/representations` | `limit`, `offset` | Phase 12 plans, including the recorded decision and capability/delivery status. |
| `GET /learners/{learner_id}/representations/{plan_id}` | — | One plan constrained to the requested learner. |
| `GET /learners/{learner_id}/trajectories` | `limit`, `offset` | Durable API-authored trajectories. Phase 13 report samples are not imported. |
| `GET /learners/{learner_id}/trajectories/{trajectory_id}` | — | Current durable trajectory snapshot. |
| `GET /learners/{learner_id}/trajectories/{trajectory_id}/history` | `limit` 1–100 (default 50), `offset` | Append-only event records ordered by event order. |
| `GET /learners/{learner_id}/diversions` | `limit`, `offset` | Durable diversion records, currently none are created by HTTP operations. |
| `GET /learners/{learner_id}/diversions/{diversion_id}` | — | A persisted diversion record, if one exists. |

## Supported trajectory writes

`POST /learners/{learner_id}/trajectories` creates a Phase 13 trajectory. Required body fields are `target_concept_id` and caller-supplied `primary_learning_goal`. Optional fields are `target_skill_ids`, `learning_objectives`, `previous_representation_plan_id`, `previous_cognitive_state_id`, and `supporting_evidence_ids`. Any supplied state/evidence reference must exist in the configured artifact index and belong to the same learner. The API does not infer a goal or prerequisite.

`POST /learners/{learner_id}/trajectories/{trajectory_id}/actions` accepts `action: "activate" | "pause" | "advance_step"`. `pause` requires a nonempty `reason`; `evidence_ids` can be attached to pause/step actions only when they resolve to that learner. Phase 13 validates each transition. Invalid transitions return 409. Current state is updated with an optimistic version check, while old versions/events remain unchanged.

No diversion creation/update/closure/resumption write endpoints are exposed. Phase 13 has internal methods for those operations, but this API does not yet have a configured, source-backed dependency registry and durable diversion workflow. The read endpoints remain available for persisted records.

## Data model details

- Phase 9–12 records are returned in their existing schema shape. Phase 9 schema version is `1.0`; Phase 10–12 source schemas are likewise preserved.
- Evidence `grouping_information` contains original Phase 10 group records. `alignment_links` contains only original group links involving that evidence ID. `grouping_annotations_available` distinguishes an indexed empty result from an unindexed group artifact.
- Representation delivery is represented only by the plan's `decision.selected_representation`, `decision.selected_action`, `decision.delivery_status`, and `decision.capability_reference`. A recommendation does not imply execution.
- Trajectory history event `trajectory_version` can repeat for same-version decisions, as defined by Phase 13. `event_order` is an API/database ordering field and is not added to the Phase 13 event payload.

Path IDs are limited to 1–160 ASCII letters, digits, `.`, `_`, `:`, and `-`. Evidence filtering currently supports `evidence_type`; richer timestamp filtering is not implemented.

## Availability and status codes

`404` means the requested learner/resource is absent. `409` means an invalid state transition, version conflict, or duplicate resource. `422` means invalid input or a mismatched source reference. `503` means the database is unavailable or a configured artifact index is absent/stale. `500` is a generic internal failure. Error messages do not include tracebacks or filesystem paths.
