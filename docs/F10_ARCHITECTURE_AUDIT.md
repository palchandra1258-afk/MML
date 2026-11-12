# F10 Architecture Audit

## Audit scope and repository safety

This audit was completed before F10 implementation. It inspected the current working tree, Student Studio API/persistence, canonical Phase 10 evidence construction and validation, Phase 9 state builder and bridge, Phase 11 estimator and schema, Phase 12 taxonomy/planner/capability registry, Phase 13 builder/manager/dependency detector, Phase 14 API and persistence services, current OpenAPI, frontend services and Student Studio/research surfaces, and the F9, Phase 14, F6, and F8 reports.

The working tree already contains extensive uncommitted F8/F9 and earlier project work across the backend, frontend, docs, migrations, shared OpenAPI contract, and tests. F10 must preserve these changes and all existing research assets. The current schema head is `0002_learning_studio`; any F10 database changes must be additive in a new migration. No implementation files were changed as part of this audit.

## Existing activity and data-source lifecycle

### Student identity and saved activity

F9 uses the fixed profile ID `studio-local-demo`, profile type `local_demo`, and a visible notice that it is not an authenticated account. It is not a `LearnerReference` and is not sourced from EdNet. F9 persists:

- `studio_profiles`: the local demonstration profile.
- `studio_learning_sessions`: lesson session, content version, start and activity timestamps.
- `studio_lesson_progress`: section checkpoints, current section, revision and completion timestamps.
- `studio_learning_attempts`: append-only evaluated answers, client submission ID, profile event sequence, content version, feedback, event timestamp, and an embedded canonical evidence JSON record.

Attempts have unique constraints on `(profile_id, submission_id)`, `(profile_id, question_id, attempt_number)`, and `(profile_id, event_sequence)`. An exact retry returns the saved feedback; reusing a submission ID for a different answer returns `409`. The route commits after `LearningService.submit_answer` returns. Answer and its normalized evidence JSON are currently persisted in the same attempt row and transaction. The route/service does not currently persist state-processing status, a Phase 9 snapshot/version, cognitive snapshots, plans, recommendations, or a recoverable work item.

### Existing evidence record

`LearningService.submit_answer` calls `base_record` with `source_dataset="mcp-ri-student-studio"`, the fixed demo profile as `learner_id`, attempt ID as `source_record_id`, question/lesson/topic/course/content identifiers and correctness in `content`, and server answer-submission time as `event_timestamp`. `base_record` uses the existing Phase 10 v1 schema and supplies distinct `ingestion_timestamp` and `processing_timestamp`, processing provenance/version, quality and uncertainty fields, and a stable evidence ID. `evidence_schema.validate_evidence` is the canonical validator. The record keeps the submitted response in evidence content and in the immutable attempt; it is not inserted into the research JSONL artifact index.

The existing `GET /studio/evidence` reads evidence embedded in attempts. There is no separate F9 processing-status field or evidence table/index. The existing artifact index is a byte-offset index over configured research JSONL files and is not an appropriate writer for Student Studio records.

## Phase 9 behavioral state

`phase9_row_from_interaction` accepts only interaction evidence and maps its learner ID, sequence number, event timestamp, question ID, correctness, skill IDs and duplicate flag to the Phase 9 row contract. `apply_interaction_evidence` validates learner identity and calls the same `LearnerStateAccumulator.update()` used by research workflows.

The accumulator computes total and labeled interactions, overall historical/recent correctness, Beta-smoothed performance, Wilson interval, evidence sufficiency/confidence/uncertainty, trend and potential issues. Its `skill_ids()` prefixes values with `ednet_skill:`. Student Studio deliberately stores `skill_ids: []`, because curriculum topic IDs are not a validated EdNet skill mapping. Therefore Studio state can summarize overall recorded response behavior but has no concept states. The current `GET /studio/behavioral-state` replays all profile attempts on each read, returns one aggregate snapshot, and adds explicit limitations. It does not save state versions or list supporting evidence IDs.

This replay is already learner-scoped and does not scan EdNet, but it is not incremental persistence. The new flow can safely recompute only this small, isolated profile stream in event sequence order within the answer transaction, then append an immutable Studio state version referencing the exact evidence prefix. No Studio data should be added to `ArtifactRecord`, research learner records, EdNet JSONL, or historical evaluation inputs.

## Phase 11 cognitive-state boundary

`estimate_cognitive_state()` requires a schema-valid Phase 9 snapshot plus a complete matching chronological Phase 10 interaction prefix. It checks learner identity, contiguous unique sequence numbers, total and labeled counts, timestamp match, and per-concept evidence-to-attempt consistency. It can emit provisional rule categories and hypotheses only for concepts already represented in Phase 9 `concept_states`; the estimator does not add construct-valid cognitive labels. Its own limits state that categories are behavioral projections, not diagnoses, and confidence is capped without ground truth.

Studio's evidence prefix is structurally suitable for the estimator's Phase 10 evidence input, and an overall Phase 9 state can be schema-valid. However, because Studio evidence has no validated skill IDs, the Phase 9 concept list is empty. The estimator can at most emit a no-concept generic diagnostic suggestion; it cannot create a topic-linked cognitive estimate or defensible concept hypothesis. Treating a curriculum topic ID as an `ednet_skill:` ID or representing a wrong answer as a misconception would violate the current contracts. F10 should expose an explicit cognitive integration availability/limitation result for Studio, rather than persist or display an invented cognitive state. The endpoint should make clear that no concept-linked cognitive estimate is available for this evidence mapping.

The existing research API only reads indexed Phase 11 artifacts. It does not run the estimator on demand or save app-authored cognitive snapshots.

## Phase 12 representation boundary

The Phase 12 taxonomy contains eight categories. `RepresentationAvailabilityRegistry` defaults every category to `unavailable` unless an actual provider ID or concrete content IDs are registered. The default reason is that no delivery provider or concept-grounded source is implemented. `build_representation_plan()` requires a validated Phase 11 cognitive state and a concept ID; optional Phase 9/evidence inputs are cross-checked. A created plan is a non-executing decision and cannot claim delivery when capability is unavailable.

The existing F6 evaluation reports all eight capabilities unavailable, zero selected representations, and plans that request diagnostic evidence or defer. The curated F9 catalog has lesson formats and objective question practice, but no adapter registers those assets against the Phase 12 taxonomy as a concept-grounded delivery capability. With no Studio Phase 11 concept estimate or approved mapping, Phase 12 cannot safely build a topic-specific Studio plan. Keep the existing lesson engine and recommendations as separate supported activity behavior; do not relabel a lesson as a Phase 12 delivered representation. An explicit unavailable status is the truthful Studio-facing integration result.

The existing research API only reads indexed Phase 12 plans; the planner is not currently exposed as a live student endpoint.

## Phase 13 trajectory boundary

`build_trajectory()` requires a learner ID, target concept ID, and caller-supplied primary goal; it accepts optional authored objectives, prerequisites, progression and evidence/state references. The HTTP `TrajectoryService` validates references against research artifact indexes, creates a `LearnerReference`, and commits snapshots, immutable versions and append-only events in a transaction. Its API exposes create, activate, pause, and advance-step operations. Diversion creation/resolution internals are not exposed through HTTP.

The `ConceptDependencyRegistry` is empty by default, validates provenance/status, and excludes synthetic dependencies in production mode. `detect_diversion()` requires matching states/evidence and a supported dependency; absent dependencies it requests more evidence and does not divert. The bounded Phase 13 report records zero diversions because the real dependency registry is empty. Student Studio has no validated prerequisite graph and no researcher/student-authored trajectory goal. Do not create an automatic trajectory from lesson order, objectives, or response correctness. F10 may report that no supported Studio trajectory exists and continue to use the actual lesson progress/curriculum records as recommendation inputs.

## Current API and persistence surface

The generated `shared/api-contracts/openapi.json` includes health; research learner, Phase 9 state, Phase 10 evidence, Phase 11 cognitive, Phase 12 representation; trajectory/diversion reads and supported trajectory mutations; F9 curriculum, profile, sessions, progress, answer, history, evidence and behavioral-state endpoints. It has no Studio state-version, cognitive availability, representation availability, trajectory status, recommendation, or research-source-filter API.

All API endpoints use the standard success/error envelope, request ID middleware, Pydantic schemas and the shared SQLite database. `learning_router` is included alongside the research router. `0002_learning_studio` is additive to `0001_initial`; attempt rows are separate from research `ArtifactRecord` rows. The runtime application database already contains research artifact indexes and should not be rebuilt, reset, or reindexed as part of F10.

## Frontend and research surfaces

`frontend/lib/services/learning.service.ts` covers curriculum, lesson, practice, demo profile, session, progress, answer, aggregate progress and history. It currently does not expose F9 evidence or behavioral state, although the backend routes exist. Separate typed clients cover research behavioral state, cognitive state, evidence, representations and trajectory. Those clients use the common API client and query the read-only research API by selected research learner ID.

The Student Studio is rendered by `StudentStudioClient` for `/studio`, exploration, subject, topic, lesson, practice, progress and history routes. Existing answer UI shows server correctness and explanation. It has no evidence/state processing status or personalized recommendation component. The research Evidence Explorer is driven by the artifact-backed `EvidenceService`; synthetic demonstrations are separately labeled. Research and evaluation screens consume saved report snapshots and explicitly distinguish EdNet experiments from synthetic engineering validation. Student Studio attempts must be surfaced through a clearly separate source classification and must not alter those historical evaluation snapshots or metrics.

## Safe F10 integration plan and acceptance boundary

1. Keep the existing immutable attempt and canonical Phase 10 record. Ensure evidence is validated before commit and expose an explicit stored/processed status. Use the attempt's existing unique submission ID and source record ID for idempotency; do not add a second evidence writer into the EdNet artifact index.
2. In the same answer transaction, recompute the isolated demo learner stream with `LearnerStateAccumulator`, append a versioned snapshot and its ordered supporting evidence IDs, and update answer feedback with the committed evidence/state status. If state/evidence validation or persistence fails, roll back the answer transaction or leave an explicit recoverable failure/pending state; never return a successful state update without a committed snapshot.
3. Return Phase 11 and Phase 12 as explicitly unsupported for topic-linked personalization until a validated Studio topic-to-skill/concept mapping and real delivery capability exist. Preserve any future provisional/hypothesis contract and uncertainty if those inputs become available; do not infer either now.
4. Do not create or mutate Phase 13 trajectories for the demo profile without an authored objective and supported dependency/state inputs. Report no automatic trajectory/diversion as a capability limitation, not a successful no-op transition.
5. Build a small deterministic recommendation from actual Studio activity/progress and available curated content only. Attach recommendation to the immutable state version and exact evidence IDs used. Keep the rule's scope in its reason and limitations; if no direct, supported basis/content exists, return exactly “More learning evidence is needed before a personalized recommendation can be made.” Generic catalog browsing suggestions remain labeled general and separate from personalized recommendations.
6. Add a student-facing feedback/status panel and a separate Student Studio evidence source view/filter in the Research Workspace. Keep EdNet and synthetic-fixture source choices distinguishable and leave historical experiment artifacts untouched.
7. Add an additive migration, typed response schemas and routes only for genuinely missing functions, then regenerate OpenAPI from the implementation. Test duplicate retries, transaction failure/rollback or recovery, evidence/state provenance, historical versions, profile isolation, downstream unavailable boundaries, recommendation provenance/fallback, frontend status and source labeling, and the full persisted workflow.

The existence of a validated Phase 9 behavioral response summary and an explainable activity recommendation does not establish understanding, mastery, cognitive diagnosis, representation benefit, or learning gain. Authentication and multi-user identity are also absent; `studio-local-demo` remains a local demonstration profile.
