# User personas and journeys

## Personas

### Learner
Wants to understand what to do next and why, without needing to understand statistical modeling. Needs concise explanations, visible progress grounded in actual activity, a calm experience when evidence is limited, and clear continuity if the lesson pauses for a supporting concept. Must not be shown internal IDs, Beta priors, raw confidence scores, or provisional categories without plain-language context.

### Researcher / administrator
Investigates whether system decisions follow the implemented rules and whether records are traceable. Needs filters, provenance, evidence windows, contradictions/missingness, versions, rule traces, rejected alternatives, availability, and explicit evaluation scope. Technical identifiers and model metrics are useful here. “Administrator” does not imply authorization capabilities at this stage.

### Product/research reviewer (secondary)
Reviews scientific claims, UX language, data lineage, and what is implemented versus planned. Needs accessible limitation notes and links from product-facing summaries to evidence and evaluation details.

## Journey A — New learner enters

| Step | Screen/action | Data and dependency |
|---|---|---|
| 1 | Overview shows supplied current objective, current trajectory status, and what is available. | Requires a backend learner/session/trajectory resource and actual objective/content mapping. Until defined, use a marked synthetic scenario or an honest empty state. |
| 2 | Learner selects “Continue” only when an executable activity/content reference is returned. | Representation/content availability. Current registry has no executable capability; do not route to fake practice. |
| 3 | Workspace presents supplied explanation/activity and the objective in context. | Content provider and content IDs, absent today. |
| 4 | Learner answers/interacts using a real supported interaction. | Activity submission contract and persistence endpoint, pending Phase 14. |
| 5 | Feedback clearly separates correctness from interpretation. | Response result; should not claim understanding. |
| 6 | Updated progress appears only after persisted response/state refresh. | State/trajectory update endpoint and server version/time. Show stale/loading/error states accurately. |

Screens: overview → learning workspace → feedback/progress. Interactions: continue, submit supported answer, inspect objective, return to path. No step is executable in current app beyond a future demo with labeled fixtures.

## Journey B — Possible difficulty and next action

1. Learner activity produces a persisted event; source/time/provenance are retained.
2. Behavioral summary updates observed correctness, recent windows, skill counts, and uncertainty. It does not measure understanding.
3. Cognitive estimator emits a versioned provisional category/hypothesis, evidence references, uncertainty dimensions, contradictions, and diagnostic recommendations.
4. Representation planner evaluates rule trace, objective/content grounding, availability, alternatives, and limitations.
5. If a supported action exists, learner sees an appropriate next step; with present availability registry the honest outcome is deferred/request-more-evidence, not a fabricated lesson.
6. Researcher can open the estimate and traverse source evidence.

Screens: workspace/feedback, learner overview, cognitive estimate detail, representation decision, evidence detail. Required backend dependencies: write interaction, read updated state, create/read estimate and plan, and evidence lookup; exact contracts pending OpenAPI. UX: avoid alarm language and offer learner agency where actions are available. Scientific condition: flags such as repeated recent incorrect responses are screening signals, not diagnoses.

## Journey C — Temporary diversion and resumption

1. Learner is on a primary trajectory with a supplied goal/current step.
2. New state/plan/evidence are evaluated. Contradiction, sparse evidence, unavailable representation, or missing explicit dependency must not trigger a diversion.
3. A diversion is created only when the backend records a supported decision and explicit prerequisite/supporting relationship. The UI explains this as a diagnostic review, not a confirmed gap.
4. Show original goal, exact interrupted step, parent version, reason/evidence, supporting concept source, bounded diversion progress, and preserved context.
5. After progress evidence, show the recorded outcome: continue diversion, ask for evidence, resume same step, resume with an available alternative, or replan. Do not translate operational thresholds into “mastered.”
6. On resumption, return to the preserved original step and show the new trajectory version; history remains inspectable.

Screens: path, diversion detail, supporting workspace (only if deliverable), resume confirmation/status, history. Dependencies: trajectory/diversion/context/history API and actual content delivery. Current Phase 13 has in-memory history and zero diversions in its bounded real-data run because the registry is empty; examples of diversion should be explicitly synthetic. UX priority: continuity and an explanation of what will happen to the original lesson.

## Journey D — Researcher investigates a decision

1. Select a learner record/run (with permitted pseudonymous identifier).
2. Inspect Phase 9 observed behavior, denominators, windows, tags and missing mappings.
3. Inspect Phase 11 versioned estimates, hypotheses, evidence links, uncertainty, contradictory evidence, and changes.
4. Open Phase 12 plan; examine objective grounding, selected/deferred action, all alternatives, availability, rule trace and rejected reasons.
5. Inspect Phase 13 primary trajectory/diversion, exact context snapshot, history versions, detector/resumption outcome, and registry edge provenance.
6. Open evidence and evaluation artifacts to confirm source and study limitations.

Screens: research overview → learner record → state/estimate → representation plan → trajectory/history → evidence detail. Dependencies: paginated search and record endpoints, stable references, artifact/evaluation endpoints, and versioned history. UX: preserve breadcrumbs, IDs, source run, timestamps and back navigation; distinguish source event timestamps (EdNet shifted question-given timestamps) from ingestion/generation time. No UI should imply the report sample estimates population effects.
