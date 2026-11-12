# Representation Decision Methodology

## Inputs and thresholds

The decision engine consumes a validated Phase 11 cognitive state. Each concept estimate carries the observed Phase 9 attempts, accuracy, trend, evidence sufficiency, potential-issue flags and source IDs. A direct Phase 9 state is optional; when supplied, the engine checks learner, timestamp and concept statistics against Phase 11. Evidence sufficiency of `none` or `low`, fewer than five attempts, a missing concept estimate, or no concept-linked evidence blocks a representation change. The operational minimum of five attempts is reused from Phase 11; Phase 9 calculations are unchanged.

The plan confidence remains `low` because no representation assignment, preference label, or post-intervention outcome exists.

## Rule order and candidate policy

1. **Conflict:** preserve contradictory evidence and request diagnostic evidence. Do not pick a winning source.
2. **Insufficient evidence/coverage or inconsistent responses:** request a concept-linked diagnostic or reasoning observation; do not make a strong representation change.
3. **Explicit representation-difficulty annotation:** consider an alternative only if a human annotation names the affected representation and explicitly names a different suggested representation. Without that detail, request clarification. No general modality preference is inferred.
4. **Repeated incorrect responses:** consider a worked example, simplified text, then diagnostic evidence. The reason explicitly says errors do not identify a cause or establish effectiveness.
5. **Declining performance:** consider a simpler worked example, a different explanation, and diagnostic evidence; add a prerequisite check because EdNet does not provide prerequisite mappings. If repeated errors also apply, both rules are retained and the candidate list combines them.
6. **No active difficulty rule:** continue the current representation only if a current type is recorded and its capability is available; otherwise defer.

Candidates are checked against the registry in policy order. Only `available` candidates with a provider/content reference may be selected. If none of the candidates can be supplied, the plan selects no representation and records an evidence-gathering action or defers until a capability exists. Rejected options carry explicit availability and reason fields.

## Context and temporal updates

Plans keep the concept, objective, current representation, trajectory ID, branch return pointer and prior diagnostic references. An updated plan links to the prior plan, increments its version, preserves those context fields and unions prior evidence history with new references. `RepresentationPlanHistory` keeps immutable copies and rejects gaps, wrong-learner plans, context loss and duplicate IDs. It does not implement diversion orchestration or actual exposure recording.

## Assumptions and limits

- Status rules describe response history, not learner cognition.
- A human mismatch annotation is not independently validated by the planner.
- No representation is considered effective based on EdNet correctness.
- The taxonomy is an interface, not a claim that these representations exist in the current product.
- EdNet item metadata has skill tags and reference IDs, not curriculum objectives or prerequisites.
- All recommendations are for a downstream component or researcher; this phase has no user-facing interaction engine.
