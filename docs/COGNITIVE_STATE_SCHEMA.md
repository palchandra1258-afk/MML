# Cognitive-State Schema v1

`schemas/cognitive_state_v1.schema.json` is a separate contract from the Phase 9 behavioral state schema. Its `estimated_learning_status` values are provisional rule outputs, not psychological diagnoses or validated measures of mastery.

## Main fields

| Field | Contents |
|---|---|
| Identity | Schema version, deterministic `cognitive_state_id`, learner ID, generation time, source `state_timestamp`, version and previous state ID. |
| Observation window | Chronological prefix counts, labeled count, source sequence bounds and event-time bounds. |
| Evidence references | IDs plus type, dataset, source file, source record ID, event time and sequence for every supplied record. |
| Observed summary | Phase 9 interaction/performance observations, available/missing modalities, conflict IDs and source provenance. |
| Concept estimates | Observed counts, accuracy, Phase 9 trend/interval/evidence tiers, provisional status, low-scoped estimate confidence, rationale and evidence IDs. |
| Difficulty hypotheses | Type, concept, support and contradictory evidence IDs, ordinal support, uncertainty reason and investigation status. The type set does not include a misconception diagnosis. |
| Uncertainty | Evidence, temporal, modality, inference and overall uncertainty, each with its own reasons. |
| Diagnostic recommendations | Suggested questions or clarification, linked to supporting hypotheses/evidence. These are recommendations only. |
| State change summary | Status changes, newly emitted/no-longer-emitted hypotheses and evidence IDs added since the prior state. |

## Status values

- `insufficient_evidence`
- `possible_difficulty`
- `developing_performance`
- `relatively_consistent_performance`
- `requires_diagnostic_investigation`

The schema reserves hypothesis type `possible_representation_difficulty`; the engine emits it only when a caller provides a human annotation with `annotation_type="human"`, the matching hypothesis/concept, annotator ID and method. Unannotated text, audio or visual evidence cannot generate that hypothesis.

## Confidence separation

`estimate_confidence` is currently `low` for EdNet-only estimates. `confidence_scope` explicitly limits it to support for the provisional behavioral category, not a cognitive probability. The prior Phase 9 behavioral confidence is included separately in `observed_performance.phase9_behavioral_confidence`. Hypothesis `confidence_or_support_level` is ordinal evidence support and is not calibrated probability.

## Validation

`src/mcp_ri/cognitive_state/state_schema.py` runs Draft 2020-12 validation (when `jsonschema` is installed) and semantic checks: IDs are unique; concept IDs match estimates; all hypothesis/recommendation references exist; conflict count matches conflict IDs; response counts add up; and each estimate has traceable supporting evidence. The builder additionally requires a complete Phase 10 interaction trace matching the Phase 9 event/label/concept counts, checks contiguous source sequence where available, and rejects records after a requested cutoff.
