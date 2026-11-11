# Resumption Engine Methodology

## Outcomes

The engine returns one of `RESUME_ORIGINAL_STEP`, `RESUME_WITH_ALTERNATIVE_REPRESENTATION`, `CONTINUE_DIVERSION`, `REQUEST_ADDITIONAL_EVIDENCE`, `REPLAN_PARENT_TRAJECTORY`, or `MARK_TRAJECTORY_COMPLETED` with a rule ID, evidence IDs, explanation, and `mastery_claim=false`.

## Evidence rules

- No diversion-concept estimate, unresolved contradictory evidence, or inadequate observation support requests additional evidence.
- At least ten labeled supporting-concept attempts, moderate/high evidence sufficiency, recent accuracy of at least 0.80, no declining trend, and Wilson interval width at most 0.45 are required for a return recommendation.
- If the evidence is sufficient to assess but misses the recent-performance/trend/uncertainty checks, continue the diversion.
- If the return checks pass and a different executable Phase 12 plan exists for the preserved parent concept, recommend resumption with that representation. A capability being available does not prove it was delivered; the reference remains a recommendation.
- A caller may explicitly request completion or replanning. Those workflow actions are recorded separately and do not assert mastery.

One correct response cannot satisfy the minimum evidence count. The checks are conservative software thresholds, not educationally validated mastery criteria. They use Phase 9 confidence intervals and Phase 11 evidence categories and preserve contradictory evidence.

## Bounded continuation

The default manager accepts at most three distinct progress evaluations per diversion. Once the limit is reached, unresolved cases require an explicit human decision to close or replan; the system will not keep creating automatic progress loops.
