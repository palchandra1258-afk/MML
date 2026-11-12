# Phase 11 Evaluation

## Real-data experiment

The bounded runner used `split_unseen_learner=validation` only. It selected the first 100 validation learners in processed source order, replayed each learner's chronological prefix, and emitted snapshots at 5 and 10 labeled responses when available (100-interaction cap). This is a coverage smoke sample, not a random sample or population-performance estimate. It scanned 105,805 table rows and normalized 824 interaction rows into 184 cognitive-state snapshots: 100 version-1 snapshots and 84 version-2 updates. No locked-test examples were evaluated.

The full `cognitive_states.jsonl` output remains local and is excluded from Git because it contains learner-level records. The aggregate run summary is [`evaluation.json`](../results/reports/phase11-cognitive-state-20261106T104113Z/evaluation.json).

| Descriptive count | Result |
|---|---:|
| Concept estimates | 1,910 |
| `insufficient_evidence` | 1,853 |
| `possible_difficulty` | 40 |
| `developing_performance` | 17 |
| `relatively_consistent_performance` | 0 |
| `requires_diagnostic_investigation` | 0 |
| Overall uncertainty high | 184 / 184 states |
| States with interaction and temporal-history evidence | 184 / 184 |
| Text/audio/visual learner evidence | None in real data |

The high insufficient-evidence count is expected from early checkpoints and sparse per-skill attempts. The sample contains no explicit conflicts, so it does not exercise conflict-driven status changes on real data. Synthetic tests cover both conflict and multimodal adapter paths.

Runtime was 8.21 seconds with peak RSS 27,236 KiB (about 26.6 MiB). The separate validator checked all 184 records and version links. The generated category and hypothesis counts are summaries of deterministic rules, not estimated model accuracy.

## Synthetic and automated validation

Fifteen focused tests cover: insufficient evidence; repeated errors; declining trends; consistent observed performance; evidence traceability; raw text not being semantically interpreted; explicit human representation annotation; unresolved contradiction handling; reference-only audio missingness; all five evidence types sharing the schema; future-sequence rejection; exact count/trace requirements; append-only temporal updates; and hypothesis/recommendation ID integrity.

Text/audio/visual fixture integration is synthetic. There are no verified learner explanations, speech files or images in EdNet. The Phase 11 estimator does not run ASR/OCR or a learned model.

## Interpretation limits

There is no direct cognitive label, external expert rating, diagnostic-intervention outcome or validated concept ontology. Thus accuracy, calibration, construct validity and misconception detection cannot be measured. The experiment shows that evidence can be traced, deterministic rules can be applied and state versions can be appended without altering Phase 9. It does not show that a rule category identifies a learner's mental state or that a suggested diagnostic is beneficial.

## Reproduction

```bash
python3 -m unittest discover -s tests/test_cognitive_state -v
python3 scripts/cognitive_state/build_cognitive_state_sample.py --sample-learners 100 --checkpoints 5 10
python3 scripts/cognitive_state/validate_cognitive_states.py results/reports/<run>/cognitive_states.jsonl
```
