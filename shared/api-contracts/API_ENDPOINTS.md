# API Endpoints

See the generated [`openapi.json`](openapi.json) for exact schemas and parameters. The frontend base URL is `http://127.0.0.1:8000/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Database, API, and per-module readiness. |
| GET | `/learners` | Paginated learner IDs and data availability. |
| GET | `/learners/{learner_id}` | Learner data availability and trajectory count. |
| GET | `/learners/{learner_id}/state` | Phase 9 behavioral snapshot. |
| GET | `/learners/{learner_id}/cognitive-state` | Latest Phase 11 estimate. |
| GET | `/learners/{learner_id}/evidence` | Paginated evidence, optional `evidence_type`, group/alignment links. |
| GET | `/learners/{learner_id}/evidence/{evidence_id}` | Single evidence record and annotations. |
| GET | `/learners/{learner_id}/representations` | Paginated Phase 12 plans. |
| GET | `/learners/{learner_id}/representations/{plan_id}` | One plan. |
| GET | `/learners/{learner_id}/trajectories` | Paginated durable trajectories. |
| GET | `/learners/{learner_id}/trajectories/{trajectory_id}` | Current snapshot. |
| GET | `/learners/{learner_id}/trajectories/{trajectory_id}/history` | Paginated append-only history. |
| POST | `/learners/{learner_id}/trajectories` | Create using a caller-supplied target and learning goal. |
| POST | `/learners/{learner_id}/trajectories/{trajectory_id}/actions` | Phase 13 `activate`, `pause`, or `advance_step`. |
| GET | `/learners/{learner_id}/diversions` | Paginated persisted diversions. |
| GET | `/learners/{learner_id}/diversions/{diversion_id}` | One persisted diversion. |

List endpoints accept `limit` and `offset`; limits are 1–100. Trajectory history defaults to 50. Responses wrap results in `success`, `data`, and `request_id`. See [DATA_MODELS.md](DATA_MODELS.md) and [ERROR_FORMAT.md](ERROR_FORMAT.md).

No diversion mutation endpoint is available. Phase 12 plans are recommendations, not evidence that content was delivered. Artifact responses are unavailable with HTTP 503 until indexed or when their source file changes.
