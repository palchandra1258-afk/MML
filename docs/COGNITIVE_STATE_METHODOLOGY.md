# Cognitive-State Estimation Methodology

## Reused Phase 9 observations

The estimator consumes a Phase 9 snapshot and does not recalculate or modify its Beta(1,1) smoothing, Wilson intervals, recent windows, ±0.10 trend threshold, evidence tiers, or potential-issue flags. It copies the observed historical/recent response performance and statistical interval into the cognitive-state record, with their source meaning retained.

Before producing estimates, it verifies that:

1. Every evidence record belongs to the Phase 9 learner.
2. The number of interaction records equals Phase 9 `total_interactions`.
3. The number of binary correctness values equals Phase 9 labeled responses.
4. Each skill's labeled evidence count equals its Phase 9 attempts.
5. The Phase 9 timestamp matches the last nonmissing source event time.
6. Where sequence numbers are available, they have no duplicates/gaps and honor the requested cutoff.
7. Conflicts refer only to supplied evidence records.

These checks require an event-complete prefix for a state snapshot. The Phase 11 sample builder replays each selected learner from source row order through a labeled-event checkpoint, then normalizes the same rows through Phase 10. This prevents a full-history Phase 9 snapshot from being paired with earlier evidence or future data.

## Transparent concept rules

Rules run in this order:

1. **Requires diagnostic investigation:** a conflict involving the concept is present. Both sources and IDs remain attached; no winner is selected.
2. **Insufficient evidence:** fewer than 5 labeled attempts. The system emits an `insufficient_concept_evidence` hypothesis when interaction evidence exists.
3. **Possible difficulty:** at least 5 attempts and any Phase 9 repeated-incorrect, recent-decline or inconsistency flag is present, or observed historical accuracy is at or below 0.50. The status wording remains “possible” and recommendations ask for more evidence.
4. **Relatively consistent performance:** at least 20 attempts, historical and recent accuracy each at least 0.80, Phase 9 trend stable or improving, no Phase 9 potential-issue flags, and Wilson 95% interval width no greater than 0.40.
5. **Developing performance:** remaining cases with at least 5 attempts.

The 0.50 and 0.80 thresholds, minimum counts and interval-width cutoff are implementation rules, not educationally validated standards. Low accuracy can reflect item difficulty, guessing or other factors; it cannot identify the reason for the observed outcome. EdNet does not show which cognitive explanation is correct.

## Hypotheses and recommendations

Phase 9 signals produce traceable hypotheses: repeated incorrect responses, declining recent performance, inconsistent responses, and insufficient evidence. Explicit unresolved conflicts produce a conflict hypothesis. A `possible_representation_difficulty` hypothesis requires a caller-supplied human annotation with a concept, annotator and method; it is not generated from text/image/audio presence or from response correctness. No hypothesis type says “misconception.”

Recommendations are generated for investigation: present a short concept-aligned diagnostic question for sparse evidence, request an explanation for a response pattern, and ask for clarification when sources conflict. The module does not conduct these actions.

## Confidence and uncertainty

The estimator reports `estimate_confidence="low"` for the provisional status because no cognitive ground truth is available for calibration. It retains Phase 9's behavioral confidence as a separate observed statistic. No numerical probability of understanding is produced.

Separate ordinal uncertainty dimensions are computed:

- **Evidence:** high when records contain no construct-valid cognitive labels; unknown if no evidence is supplied.
- **Temporal:** medium when interaction source order/timestamps exist, reflecting EdNet's shifted question-given clock; high when timing/order is incomplete; unknown without interactions.
- **Modality:** based on expected modality availability. Multiple missing expected modalities produce high modality uncertainty. A reference-only audio/image asset is treated as unavailable for this summary.
- **Inference:** high because no cognitive-state target is available for calibration.
- **Overall:** the most conservative dimension, with `unknown` treated as unresolved rather than as low uncertainty.

These categories are descriptive and not calibrated probabilities.

## Temporal state versioning

`CognitiveStateHistory` appends each new state with a consecutive version and `previous_state_id`. It rejects duplicate state IDs, learner changes and decreasing source sequence. `state_change_summary` reports concept-category transitions, evidence IDs newly added, hypotheses newly emitted and hypotheses no longer emitted. Historical records are copied and remain unchanged. A hypothesis no longer emitted is not automatically marked resolved.
