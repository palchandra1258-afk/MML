# Phase 13 Trajectory Evaluation

## Scope

Evaluation covers schema validation, permitted transitions, deterministic decision rules, evidence linkage, parent-child and context links, append-only versions, and historical reconstruction. It does not measure cognitive accuracy, prerequisite mastery, learner experience, or learning outcomes. No locked-test partition is used.

## Synthetic tests

The focused suite is in `tests/trajectory/`. Synthetic fixtures exercise repeated errors, declining performance, sufficient and insufficient evidence, conflicts, manually configured and synthetic dependency edges, unavailable representation delivery, context preservation, progress updates, revisions, closure, resumption, alternative representation, replanning, completion, invalid transitions, depth/active/duplicate limits, idempotency, history reconstruction, and missing evidence references. A successful fixture is not evidence of learning improvement.

## Bounded real-data sample

The sample builder reads the bounded Phase 11 validation JSONL and optional matching Phase 12 plan JSONL. It uses at most one concept estimate per cognitive-state snapshot and an empty dependency registry unless an explicitly sourced registry file is passed. It does not read the processed interaction table, retrain models, or inspect the locked test partition. As no prerequisite map is available, the real-data run can validate continuity and conservative fallback behavior but cannot establish meaningful prerequisite diversions.

Run outputs include trajectory snapshots, diversion version records, context snapshots, history events, detector decisions, and the dependency registry. The evaluator reports valid transition rate, invalid-transition rejection, context preservation, parent-child consistency, duplicate rate, reconstruction, evidence-reference checks, resumption traceability, depth enforcement, and deterministic replay. Zero diversions make diversion-only percentages not applicable (`null`), not 100%.

The completed bounded run is [`phase13-trajectory-20261111T040954Z`](../results/reports/phase13-trajectory-20261111T040954Z/). It read 100 Phase 11 snapshots representing 55 distinct learners and created 100 primary trajectories. All 100 decisions requested additional evidence: the actual registry was empty, so no prerequisite diversion was justified. The data do not contain a trajectory/goal assignment, and sample objectives are explicitly marked unavailable.

| Measure | Result |
|---|---:|
| Trajectories created | 100 |
| Observed state transitions | 100 / 100 valid (100%) |
| Invalid state-machine edges checked | 44 / 44 rejected (100%) |
| History events | 300 |
| Unique trajectory versions reconstructed | 200 |
| Event-to-history reconstruction | 300 / 300 (100%) |
| Decision replay | 100 / 100 identical (100%) |
| Cognitive-state evidence-reference checks | 100 / 100 valid (100%) |
| Diversions created | 0 |
| Context preservation, parent-child, duplicate, resumption, and depth rates | N/A; no diversion was created |
| Locked-test examples | 0 |

`validate_trajectory_history.py` independently validated the 100 trajectory records, 300 events, and 200 reconstructed versions. These are orchestration and traceability metrics. The synthetic suite exercises nonzero diversion creation, context snapshots, progress/revision/closure, resumption, and export validation.

The Phase 13 focused suite passes 41 tests. Focused Phase 9, 10, 11, and 12 suites pass 20, 18, 15, and 21 tests respectively. Full repository discovery ran 133 tests: 130 passed, one was skipped, and two existing ML test modules errored at import because this Python 3.12.3 environment lacks `joblib` and `torch`. The failures occur before implementation assertions; the skipped training pipeline also reports missing training requirements.

## Reproduction

```bash
python3 -m unittest discover -s tests/trajectory -v
python3 scripts/trajectory/build_trajectory_sample.py --max-trajectories 100
python3 scripts/trajectory/evaluate_trajectory.py results/reports/<run> \
  --states results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl
python3 scripts/trajectory/validate_trajectory_history.py results/reports/<run>
```

The output directory uses a new UTC timestamp and refuses to overwrite an existing run.
