# Phase 12 Representation-Planning Evaluation

## Bounded real-data run

The builder consumed the existing Phase 11 validation-only JSONL and the small EdNet question/lecture metadata archive. It did not scan the 5.9 GB processed interaction table, train models, read locked-test records, or overwrite earlier reports. The run is [`phase12-representation-20261106T112420Z`](../results/reports/phase12-representation-20261106T112420Z/).

| Measure | Result |
|---|---:|
| Phase 11 snapshots read | 184 |
| Learners represented | 100 validation learners (inherited from Phase 11 sample) |
| Concept plans built | 1,910 |
| Plans with a selected representation | 0 / 1,910 |
| Diagnostic-evidence recommendations | 1,879 |
| Additional-evidence recommendations | 14 |
| Defer-until-capability recommendations | 17 |
| Alternative rejection records | 15,280 |
| Cognitive-state ID/version matches | 1,910 / 1,910 |
| Source evidence-reference matches | 1,910 / 1,910 |
| Source diagnostic-recommendation matches | 1,910 / 1,910 |
| Temporal plan links preserving teaching context | 717 / 717 |
| Locked-test examples evaluated | No |

No plan selected a representation because all eight registry capabilities are unavailable in this repository. Candidate recommendations are still recorded with rejection reasons and provider/content gaps. The real-data sample had 60 repeated-incorrect rule activations, 33 inconsistent-response activations, and 1 declining-performance activation. Conflict and representation-mismatch rules were exercised in synthetic tests because the real sample has no such applicable cases.

The independent evaluator validated every plan against the schema, linked cognitive-state ID/version and evidence/recommendation IDs back to the original Phase 11 JSONL, checked plan-version chains and confirmed preserved concept/objective/current-representation/trajectory/return context. Learner-level Phase 11 and Phase 12 JSONL files remain local and are excluded from Git. The aggregate builder record is [`build_report.json`](../results/reports/phase12-representation-20261106T112420Z/build_report.json), and the cross-check is [`evaluation.json`](../results/reports/phase12-representation-20261106T112420Z/evaluation.json).

The build took 15.782 seconds internally (16.04 seconds wall time from `/usr/bin/time`, 15.91 seconds user CPU) and peaked at 49,440 KiB RSS (about 48.3 MiB). No full interaction table was loaded.

## Synthetic policy and integration tests

Twenty-one Phase 12 tests pass. They cover taxonomy/schema, all requested evidence patterns, contradiction handling, human-annotated mismatch, capability fallback including `planned` status, selection only from available providers, alternative reasons, metadata-only EdNet grounding without answer keys, direct Phase 9 cross-checks, source traceability, and append-only context-preserving revisions, including rejection of older cognitive-state versions. These are decision-policy and software checks, not learning-effect evidence.

The Phase 9, 10, and 11 focused suites also pass: 20, 18, and 15 tests respectively. Final full discovery ran 92 tests: 89 passed, one was skipped, and two existing ML test modules errored on imports because this Python 3.12.3 environment lacks `joblib` and `torch`. The skipped pipeline module also reports its missing training requirements. Those dependencies were not installed for this phase.

## Interpretation limits

EdNet provides skill tags and question/lecture metadata references, but no validated concept names, curriculum objectives, prerequisites, example bank, or local lecture assets. Text, visual, symbolic, interactive, simulation, worked-example and diagnostic delivery are not available. A human representation annotation may support only a low-confidence candidate; it does not establish preference or effectiveness. EdNet contains no representation assignments, exposure logs or post-intervention learning outcomes, so this run measures rule execution, schema validity, capability gating, traceability and context retention only.

No claim is made about cognitive-state accuracy, optimal representation choice, learner modality preference, or improved learning outcomes.

## Reproduction

```bash
python3 -m unittest discover -s tests/test_representation -v
python3 scripts/representation/build_representation_plans.py --max-plans 10000
python3 scripts/representation/evaluate_representation_plans.py results/reports/<run>/representation_plans.jsonl --states results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl --output results/reports/<run>/evaluation.json
python3 scripts/representation/inspect_representation_plan.py results/reports/<run>/representation_plans.jsonl <plan_id>
```
