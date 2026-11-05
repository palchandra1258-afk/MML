# EdNet KT1 Data Splitting Strategy

Two independent protocols are assigned in separate columns in the same processed table. A run must select one protocol; never merge their train/validation/test labels.

## Experiment A: unseen learner generalisation

- Assign each learner by a deterministic BLAKE2 hash of `seed:learner_id`, with default seed `2025`.
- Hash buckets below 70% are training, the next 15% validation, and the remainder test. This is an approximate 70/15/15 split, not response-row randomization or class stratification.
- All target rows from a learner share one partition. No learner can cross train/validation/test.
- Feature histories remain strictly within the learner's own source sequence. No target outcome from another learner enters a history.
- Report actual learner, example, correct-target and incorrect-target counts from `ednet_preprocessing_summary.json`; proportions are approximate due to whole-learner grouping.

## Experiment B: future prediction for known learners

- Within each learner, count only target-eligible rows in source order. The first 70% of eligible targets are training, the next 15% validation, and the final 15% test using deterministic integer boundaries. If a learner has at least one eligible target, at least one target is assigned to training. Very short sequences may have no validation or test example.
- Unlabelled events remain in chronology but do not occupy a supervised split position.
- For a validation/test event, historical features may include earlier logged events and earlier submitted outcomes from that same learner, including earlier validation events before a later validation event and earlier validation/test-history events before a later test event. This matches sequential prediction for a known learner whose prior outcomes have already been observed. The current and future outcomes are never available to that row.
- The model is fit only on training targets, tuned on validation targets, and evaluated on the later test targets. State updates use observed prior outcomes at each event; no batch feature may aggregate future rows.

## Cross-protocol safeguards

- The two split labels are deliberately distinct fields: `split_unseen_learner` and `split_future_known_learner`.
- For Experiment A, a learner must occur in exactly one partition. For Experiment B, learners intentionally appear in multiple temporal partitions, but the event boundaries are ordered train, validation, test.
- Feature encoders, imputers, scalers, feature selection, model parameters and calibration must be fitted without test labels. Any target-derived history is computed online in sequence and can use only labels that precede that row.
- Do not randomly shuffle interactions before feature construction or split assignment. Source row order resolves timestamp ties.
- A development subset (`--max-learners`) is not a final evaluation set; publish the limit in its run metadata and regenerate the full artifact before baseline evaluation.

The full run's actual split counts are recorded in `data/processed/ednet/ednet_preprocessing_summary.json`. No model has been trained as part of this phase.

## Observed complete-run counts

| Protocol | Split | Learners represented | Targets | Correct | Incorrect |
|---|---|---:|---:|---:|---:|
| Unseen learners | Train | 549,251 | 66,898,246 | 43,725,275 | 23,172,971 |
| Unseen learners | Validation | 117,784 | 14,236,525 | 9,288,983 | 4,947,542 |
| Unseen learners | Test | 117,269 | 14,131,509 | 9,234,424 | 4,897,085 |
| Future known learners | Train | 784,304 | 66,348,221 | 43,180,703 | 23,167,518 |
| Future known learners | Validation | 715,712 | 14,241,038 | 9,479,258 | 4,761,780 |
| Future known learners | Test | 756,936 | 14,677,021 | 9,588,721 | 5,088,300 |

The two protocols each cover all 95,266,280 labelled targets. Five learners had no eligible target, so they appear in no unseen-learner split. Correct/incorrect totals describe target labels only and are not model performance.
