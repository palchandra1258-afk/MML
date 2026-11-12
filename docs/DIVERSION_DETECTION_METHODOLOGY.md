# Diversion Detection Methodology

## Inputs and validation

The rule engine accepts a Phase 9 behavioral state, Phase 10 evidence records, Phase 11 cognitive state, Phase 12 representation plan, current trajectory, and a `ConceptDependencyRegistry`. It validates schemas, learner IDs, cognitive-state/evidence references, and—when both are supplied—matches Phase 9 current-concept statistics against the embedded Phase 11 values. A Phase 12 plan must refer to the same learner, concept, cognitive-state ID, and version.

## Decision order

1. **No state or current-concept estimate:** preserve the primary path and request evidence.
2. **Contradictory evidence:** retain contradictory IDs and request clarification/diagnostic evidence; do not create a diversion.
3. **Representation delivery deferred:** continue the primary trajectory. Unavailable delivery is not treated as learner difficulty.
4. **Sparse evidence:** fewer than five labeled attempts or Phase 9 evidence sufficiency `none`/`low` requests more evidence.
5. **Inconsistent recent responses:** request a diagnostic observation rather than diverting.
6. **No repeated-error or declining-performance rule:** continue the current trajectory.
7. **Repeated errors or declining trend:** require concept-linked evidence and an explicit registry relationship before a diversion can be created. Without a dependency record, request evidence; do not invent one.
8. **Supporting concept already has stronger observed performance:** when there are at least ten attempts, moderate/high evidence, recent accuracy at least 0.80, stable/improving trend, and Wilson interval width at most 0.45, do not divert on a presumed gap. This operational screen is not a mastery test.

Repeated incorrect responses reuse the Phase 9 recent-window flag (at least three incorrect responses in the recent concept window). Declining performance reuses the Phase 9 latest-five versus preceding-five decrease threshold. Those flags explain why a diagnostic review may be useful; they do not identify a cause.

## Relationship provenance

The supporting concept must be linked to the current concept by `PREREQUISITE` or `SUPPORTING_CONCEPT`. The record carries a source, confidence, and verification status. Default production decisions exclude `synthetic_test` relationships. A manual relationship permits a low-confidence diagnostic review, not a claim that the relationship is a dataset observation or that the learner has a gap.

## Output

The detector returns one of `CREATE_DIVERSION`, `REQUEST_ADDITIONAL_EVIDENCE`, or `CONTINUE_PRIMARY`, with rule ID, explanation, linked evidence and state/plan references, and any selected dependency record. `TrajectoryManager` then enforces depth, active-diversion, duplicate, and scope limits before creating a child diversion.
