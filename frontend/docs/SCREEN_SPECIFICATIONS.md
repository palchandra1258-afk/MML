# Screen specifications

All routes below are proposals. Phase 14 OpenAPI contracts now exist and the F2 client covers health and learner-index reads; detailed page-to-service connections are later milestones. The current endpoint mapping is in [`F2_API_INTEGRATION.md`](F2_API_INTEGRATION.md). Shared states: loading should identify the section and use stable skeletons; empty should say which source/resource is absent; error should preserve retry/back navigation and avoid exposing internal details. Synthetic scenario data must carry a persistent banner and record-level labels.

## Recommended navigation

Learner: Overview → Learning workspace → Learning path → contextual Diversion detail → Progress. Research: Research overview → Learner record (Behavior / Estimates / Trajectory) → Representation plan → Evidence detail; plus Evidence explorer and Research & evaluation. See the information architecture for proposed paths.

## 1. Overview dashboard (`/dashboard`)

- **Objective/user:** orient learner to current supplied objective and next supported action; researchers use a separate overview.
- **Layout/components:** objective header; current step/status; progress path; next-action card; recent recorded activity; continuity card when diverted; provenance/source notice.
- **Information:** objective/trajectory only when supplied by service; progress counts and source; latest state timestamp; action availability. No arbitrary streaks, “mastery,” or decorative KPIs.
- **Interactions:** open workspace/path, review a diversion, see why an action is unavailable.
- **Data/API:** F2 currently reads `GET /health` and `GET /learners`; the API does not provide current objective, active learner session, or activity summary. Trajectory reads are learner-scoped.
- **Loading/empty/error:** skeleton; “No learning objective is assigned yet” if genuinely absent; service error with retry.
- **Responsive:** one column; path and continuity remain visible before secondary activity.
- **Scientific/UX:** EdNet states do not supply a real objective. Never use generated objectives as observed data; distinguish source event time from state generation time.

## 2. Learning workspace (`/learning`)

- **Objective/user:** present a real selected representation/activity, or explain that no executable content is available; learner.
- **Layout/components:** objective/context; content canvas; activity controls only from provider; feedback region; progress/continuity strip; request/return controls only when supported.
- **Information:** provider/content reference, current step and permitted feedback. Future types include text, worked example, visual, symbolic, interactive, simulation, diagnostic and alternative explanation.
- **Interactions:** read/view/use/submit only actual provider-supported controls; return to path; optionally request help if API supports it.
- **Data/API:** No content, session, interaction submission, or feedback endpoint exists. Present registry has all eight capabilities unavailable.
- **Loading/empty/error:** content skeleton; explicit “No executable learning activity is available”; retry/reload for errors. Do not show fake questions or disabled controls styled as live.
- **Responsive:** content-first, controls keyboard accessible, media alternatives and captions when future media exists.
- **Scientific/UX:** EdNet catalog references (question/lecture IDs) are not content. A capability recommendation does not prove delivery.

## 3. Behavioral learner-state explorer (`/research/learners/[id]/behavior`)

- **Objective/user:** inspect observed response history summaries; researcher.
- **Layout/components:** source/run header; summary counts; observed performance window; recent vs historical comparison; trend; interval visualization; skill/tag table; flags/missingness and raw-record links.
- **Information:** Phase 9 total/labeled/unlabeled interactions, mapping coverage, duplicate count, attempts/correct/incorrect, historical/recent accuracy, Beta(1,1)-smoothed response correctness, recent window, trend threshold, Wilson interval, evidence sufficiency and potential-issue flags. Prediction may be null.
- **Interactions:** choose skill, time/version if available, inspect underlying evidence; export only if backend supports it.
- **Data/API:** `GET /learners/{learner_id}/state` and paginated evidence read are available; current F2 screen is not connected yet.
- **Loading/empty/error:** summary skeleton; no state/source partition message; retry and request ID on service issue.
- **Responsive:** metric cards stack; wide skill table scrolls with persistent headers.
- **Scientific/UX:** all measures are response behavior, not ability/understanding. Intervals concern outcome proportions and can be affected by repeated-response dependence. Label skill IDs as EdNet tags, not validated concepts.

## 4. Cognitive-state explorer (`/research/learners/[id]/estimates` and detail)

- **Objective/user:** inspect versioned hypotheses and why they remain uncertain; researcher; learner-facing wording is a simpler summary only.
- **Layout/components:** “Provisional estimate” header/version; concept estimates; evidence chain; uncertainty dimensions; contradiction list; diagnostic recommendations; change history.
- **Information:** Phase 11 category/hypotheses, statement/rationale, support tier and its scope, evidence IDs, source provenance, time window, evidence/temporal/modality/inference uncertainty, missing modalities, contradictory IDs, previous state link.
- **Interactions:** open evidence record; compare previous version; filter concept; inspect recommendation.
- **Data/API:** `GET /learners/{learner_id}/cognitive-state` returns the latest saved estimate; history/version-comparison endpoints are not exposed.
- **Loading/empty/error:** skeleton; “No estimate / insufficient evidence” rather than default status; retry and preserve current filter.
- **Responsive:** single-column evidence cards; uncertainty dimensions become labeled rows, not tiny chart.
- **Scientific/UX:** categories are deterministic rule outputs without cognitive ground truth; avoid diagnosis language. Confidence is support for a behavioral category, not probability of cognitive truth.

## 5. Representation intelligence (`/research/representations/[planId]`)

- **Objective/user:** explain selection or deferral; researcher, with concise learner-safe explanation where appropriate.
- **Layout/components:** decision and delivery status; learning-objective grounding; traceable inputs; rule trace; rejected alternatives; capability status; evaluation strategy; limitation panel; linked state/evidence/trajectory.
- **Information:** selected representation nullable; downstream action; availability; rationale; decision method/confidence scope; policy trace; rejected alternatives and reasons; content grounding and IDs; objective status; suggested evaluation observation.
- **Interactions:** open source evidence, prior plan, linked trajectory; filter/check rule trace. No “launch activity” unless a provider/content reference is truly executable.
- **Data/API:** Representation list/detail reads are available under `/learners/{learner_id}/representations`; availability and delivery status are fields in each saved plan, not a separate registry endpoint.
- **Loading/empty/error:** skeleton; plan unavailable or deferred shown distinctly; errors with retry.
- **Responsive:** trace becomes vertical ordered list; alternatives accordions retain availability text.
- **Scientific/UX:** current registry marks every category unavailable. Recommendation confidence is ordinal and does not predict effect or preference.

## 6. Learning trajectory (`/learning-path`, researcher trajectory tab)

- **Objective/user:** orient learner/researcher to current goal and history.
- **Layout/components:** primary goal/current step; path timeline; completed/current/pending statuses; diversion branch; version/time selector; source/record details in research mode.
- **Information:** trajectory ID/version/status, supplied goal/concept/step, primary/child relations, events/history, plan/state references and actual recorded completion.
- **Interactions:** open step, diversion, historical version; resume action only if backend says eligible and action endpoint exists.
- **Data/API:** Trajectory list/detail and history GETs are available per learner. The API persists trajectory create and activate/pause/advance actions.
- **Loading/empty/error:** timeline skeleton; no supplied trajectory; retry.
- **Responsive:** vertical path, nested branch visually linked to parent and interrupted step.
- **Scientific/UX:** EdNet does not provide learner objectives or course sequence. A wrapper trajectory in a bounded software sample is not the learner's actual learning path.

## 7. Diversion and resumption (`/learning-path/diversions/[id]`)

- **Objective/user:** explain interruption and guarantee continuity; learner/researcher with detail level adapted.
- **Layout/components:** original goal + exact preserved step; diversion reason/status; supporting concept + relationship provenance; context snapshot; bounded progress; latest evidence; recorded recommendation/outcome; return path.
- **Information:** parent trajectory/version; snapshot ID; completed/pending steps; prior state/plan refs; evidence/recommendation IDs; dependency edge and source/status; diversion progress and max evaluations; resumption outcome.
- **Interactions:** inspect why, inspect evidence, continue/resume/replan only if a backend-provided allowed action is available; confirmation dialog preserves parent context.
- **Data/API:** GETs exist for stored diversions and trajectory history. No diversion, context-snapshot, or resumption write endpoints are exposed; no dependency-registry API is exposed.
- **Loading/empty/error:** explicit not-found/no-active-diversion; safe retry; do not infer missing context.
- **Responsive:** stacked context blocks; parent-step marker repeated near action.
- **Scientific/UX:** diversion is diagnostic review, not confirmed prerequisite gap. Operational return checks are not mastery criteria. Current default registry is empty; production sample has no diversions.

## 8. Evidence explorer (`/research/evidence` and record detail)

- **Objective/user:** trace observations and processing; researcher.
- **Layout/components:** filters; paginated table/list; timeline when timestamps comparable; detail drawer/page with provenance, content metadata, status, missing fields, quality flags, relationships, grouping/alignment/conflict panels.
- **Information:** evidence type, source dataset/file/record, event and ingestion times, temporal precision/source, sequence, modality, processing status/method/version, missingness, uncertainty, duplicate candidates, related IDs, alignment and conflict status.
- **Interactions:** filter type/source/time/status, follow relationships, inspect conflict without selecting a winner, compare aligned records.
- **Data/API:** Evidence list/detail GETs include grouping and alignment annotations where indexed. There are no standalone group or conflict endpoints; filtering currently supports `evidence_type`.
- **Loading/empty/error:** table skeleton; no records/matching filters; retry.
- **Responsive:** cards on phone; researcher table horizontally scrolls with row labels.
- **Scientific/UX:** real EdNet interaction evidence is distinct from synthetic text/audio/visual fixtures. Audio/image bytes are not embedded; transcript/OCR may be pending/failed. EdNet timestamps are shifted question-given timestamps, not submission time or real-world time.

## 9. Research and model evaluation (`/evaluation`)

- **Objective/user:** understand experiment results and data quality; researcher/reviewer.
- **Layout/components:** report inventory; model/cohort selectors; dataset/split/target metadata; metric comparison table; saved calibration-bin reliability diagram; phase validation summaries; allowlisted aggregate artifact references.
- **Information:** metrics from existing reports, evaluated target (answer correctness), validation/test protocol, training info and sample denominator. Include report date and model/version. Highlight no cognitive ground truth or post-intervention learning outcome.
- **Interactions:** select run/model, compare within a compatible cohort, inspect metric definitions and source references.
- **Data/API:** No model-evaluation or report-artifact endpoint exists. The page uses a versioned frontend snapshot of allowlisted aggregate reports, clearly marked as not live API data. No browser filesystem access or learner-level export is used.
- **Loading/empty/error:** report inventory is statically bundled; empty selections and missing calibration bins have explicit states. A static snapshot has no API retry state.
- **Responsive:** tables become labeled rows; plots include text/table alternative.
- **Scientific/UX:** correctness prediction metrics do not measure cognitive estimation, representation effectiveness, or learning gain. Never put these on learner dashboard.

## 10. Research overview/system status (`/research`)

- **Objective/user:** summarize available data and artifact readiness.
- **Layout/components:** actual-data vs synthetic-demo inventory; phase/artifact status; model run links; capability matrix; API/service status when available; limitations banner.
- **Information:** counts only with source/run/time; availability state for eight capabilities; storage/API readiness. No fabricated live service signals.
- **Interactions:** navigate into reports, data sources, configuration/limitations.
- **Data/API:** `GET /health` reports module/index/database readiness and record counts; `GET /learners` reports the paginated learner index. No report catalog endpoint exists.
- **Loading/empty/error:** distinguish absent report, offline backend, and unsupported telemetry.
- **Responsive:** cards stack, important limitations remain above fold.
- **Scientific/UX:** a successful software validation run verifies implementation properties only within scope; it does not validate cognition or learning effects.
