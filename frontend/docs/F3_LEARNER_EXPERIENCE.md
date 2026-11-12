# F3 — Learner dashboard and learning workspace

## Scope

F3 connects the overview, progress, learner state, cognitive state, trajectory, and learning workspace screens to the existing F2 API client and services. It changes only the frontend; no backend or OpenAPI files are changed. Research, evaluation, representation-only, evidence-only, and system-status routes remain on their existing planned pages. F4 has not started.

The interface treats a selected learner as a pseudonymous research record. There is no sign-in, current-user, or active-session endpoint. The selected record lives in the app-shell React context, so it is shared across navigation and is cleared on a full page reload.

## Screens and components

- **Overview (`/`)** — learner index paging and ID lookup, source record metadata, behavioral summary, cognitive estimate preview, indexed evidence, saved trajectory, representation-plan availability, and the F2 health module readiness summary.
- **Learning progress (`/progress`)** — Phase 9 response snapshot, selectable concept/skill tags, concept-level statistics and intervals, and evidence matching the exact source `skill_ids`.
- **Learner state (`/learner-state`)** — the same observed behavior and concept explorer, framed as a Phase 9 record.
- **Cognitive state (`/cognitive-state`)** — Phase 11 hypotheses, uncertainty dimensions and reasons, available/missing modalities, contradictory evidence, concept estimates, saved recommendations, references, and limitations.
- **Learning trajectory (`/trajectory`)** — stored trajectory selection, goals and steps, context references, event history, and diversion/resumption snapshots.
- **Learning workspace (`/learning`)** — saved representation-plan context and trajectory, with an explicit statement that lesson and interaction delivery are unavailable.

Shared learner components include `LearnerRecordPicker`, `LearnerPageHeading`, `SelectedLearnerSummary`, and `ApiResourcePanel`. `useApiResource` keys resource state by selected record and artifact, aborts obsolete requests, preserves request IDs, and exposes a user retry action. `loadLatestIndexedPage` selects the final source-event page for indexed artifacts whose API ordering is oldest-to-newest.

## API services and displayed fields

All requests use `lib/services` and the F2 API client. Learner views use these read routes:

| Service | API route | Fields presented |
|---|---|---|
| API health (F2 shell service) | `GET /health` | API status/version, database status, module availability/mode/record counts, response timestamp |
| Learner index/detail | `GET /learners`, `GET /learners/{learner_id}` | `learner_id`, `available_data`, `trajectory_count`, `source` |
| Behavioral state | `GET /learners/{learner_id}/state` | `observation_summary.total_interactions`, `labelled_responses`, `unlabelled_interactions`, `unique_concepts_observed`; `learning_performance.attempts`, `correct`, `incorrect`, historical/recent/estimated performance, trend, evidence sufficiency, confidence, uncertainty, interval and potential issues |
| Concept states | Same Phase 9 state response | `concept_id`, attempts/outcomes, historical/recent accuracy, smoothed performance, evidence count, trend, sufficiency, confidence, uncertainty interval/reasons, potential issues |
| Evidence | `GET /learners/{learner_id}/evidence` | evidence ID/type, source dataset/record/modality, `skill_ids`, sequence, timestamp meaning and precision, processing version/status, quality flags and uncertainty notes |
| Cognitive state | `GET /learners/{learner_id}/cognitive-state` | state ID/version/time; observed evidence counts and correctness; contradictory counts/IDs; available/missing modalities; four uncertainty levels and reason lists; hypothesis statement/type/support and supporting/contradictory IDs; estimate status/confidence/scope/rationale; recommendation action/reason/status; evidence references and limitations |
| Representation plans | `GET /learners/{learner_id}/representations` | plan ID/kind/version, concept, selected action/representation, delivery status, rationale, confidence scope, objective text/status/intended outcome, and limitations |
| Trajectory | `GET /learners/{learner_id}/trajectories` | goal, target/current concept, saved status/version, current step, completed/pending/expected steps, objectives, prerequisites, context references, orchestration references, timestamps |
| Trajectory history | `GET /learners/{learner_id}/trajectories/{trajectory_id}/history` | event type/time, previous and new state, trigger, explanation, supporting evidence IDs, related diversion ID |
| Diversions | `GET /learners/{learner_id}/diversions` | diversion status/concepts/reason, parent and context snapshot references, previous step, saved resume condition, resolution, supporting evidence IDs, progress and revision counts |

The F3 interface issues no trajectory writes. Although F2 exposes trajectory creation and action methods, the UI does not create goals, activate/pause/advance a path, submit evidence, or apply resumption decisions.

## Source, loading, and missing-data behavior

- Real mode shows only API records. A backend error never activates mock data.
- The page headings identify live API data; each loaded resource carries a source label and request ID where supplied.
- Loading, retryable error, empty response, missing artifact, and missing selected record have separate states. A 404 is rendered as unavailable data, not as a fabricated empty record.
- Mock mode requires `NEXT_PUBLIC_USE_MOCK_DATA=true`. It is visibly labeled synthetic; learner subpages do not invent state or evidence. The overview uses the existing fictional objective only as a clearly marked UI demonstration.
- Numeric fields that are absent stay “Not reported.” No time series is drawn from snapshot data.
- Learner selection is a research record lookup, not a real identity or authenticated account.

## Scientific and product limits

- Response correctness is behavioral observation, not direct understanding or mastery. Smoothed performance is labelled as an estimate; its interval applies to correctness only.
- Cognitive outputs are provisional rule-based categories with no validated cognitive ground truth. Confidence is support for a provisional behavioral category, not a probability of cognitive truth.
- Dataset skill IDs are not a validated curriculum. No prerequisite graph or causal relationship is inferred.
- Source timestamps in the inspected EdNet records are shifted question-given times, not response-submission or wall-clock learning times.
- The inspected Phase 10 evidence page can contain fewer records than the evidence references embedded in a Phase 11 estimate. The UI preserves the reference IDs and does not claim that the separate index is complete.
- Representation plans can ask for diagnostic evidence while having no selected representation, objective text, capability reference, or delivery provider. A saved recommendation is not delivered instruction.
- There is no content provider, lesson/quiz delivery, interaction submission, tutoring, feedback, live model inference, or learner session service. No activity, streak, study duration, mastery score, gain, or exam prediction is shown.
- Trajectory context snapshot IDs are displayed as references because the API has no context-snapshot retrieval route. Saved resume conditions do not mean a resumption was assessed or applied.

During the 2026-11-11 local API audit, health reported 117,785 indexed learner records. One inspected research record returned four labeled interactions, zero correct responses, ten observed skill tags, low evidence sufficiency, high uncertainty, and an insufficient-evidence trend. Its trajectory and diversion indexes were empty. A saved representation plan had no selected representation and `delivery_status: not_selected`. These are an API sample, not defaults or assumptions for other records.

## Tests and validation

Learner helper tests use Node's built-in test runner and no added package dependencies. They cover missing artifact keys, final-page loading and empty responses, concept selection and evidence matching, absent intervals, resource loading/error/retry transitions, trajectory selection, learner route registration, and the shell's mobile navigation hooks/breakpoint. The existing F2 client tests cover HTTP/network failures and no silent mock fallback.

The test suite does not mount React components in a browser DOM: no DOM/component test framework is installed. The full Next production build compiles the screens; responsive layout remains based on the existing application-shell breakpoints plus F3 mobile styles.

Validation run from `frontend/` on 2026-11-11:

- `npm run lint` — passed with no warnings or errors.
- `npm run test:api` — passed, 21 tests total (12 F2 API client tests and 9 F3 learner tests).
- `npx tsc --noEmit` — passed.
- `npm run build` — passed; Next.js generated the overview and all learner/research routes.
- `git diff --check` — passed from the repository root.
