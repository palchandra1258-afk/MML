# EdNet KT1 Baseline Experiments

## Task and evaluation boundary

Predict whether the submitted answer to a presented question will match the official answer key. This is a behavioral response-outcome task, not a direct measurement of understanding, confusion, or cognitive state. The primary comparison used the **unseen-learner validation split**: 14,236,525 target examples from 117,784 validation learners. The test split was not scored or used for selection.

The validation set contains 9,288,983 correct targets (65.2475%) and 4,947,542 incorrect targets (34.7525%). This class imbalance makes accuracy alone insufficient.

## Baselines

1. **Majority/prevalence:** probability of correctness is the full training split prevalence (43,725,275 / 66,898,246); predict correct at the fixed 0.5 threshold. This predicts correct for every case.
2. **Last-response persistence:** use the most recent earlier labelled response's correctness as probability 0 or 1. For cold start, use full training prevalence.
3. **Historical-accuracy persistence:** use the learner's prior accuracy as probability; for cold start, use full training prevalence.

The persistence features come from strictly earlier rows. The hard last-response baseline is highly overconfident when wrong; its log loss and ECE reflect that.

## Validation results

F1, precision, and recall use correctness (`1`) as the positive class. The decision threshold is fixed at 0.5 for every method. PR-AUC is average precision. Confusion matrices use true rows/predicted columns in label order `[incorrect 0, correct 1]`.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC / AP | Log loss | Brier | ECE (15 bins) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Majority/prevalence | 0.6525 | 0.6525 | 1.0000 | 0.7897 | 0.5000 | 0.6525 | 0.6459 | 0.2268 | 0.0011 |
| Last-response persistence | 0.5974 | 0.6902 | 0.6950 | 0.6926 | 0.5556 | 0.6794 | 13.7975 | 0.4013 | 0.3997 |
| Historical accuracy | 0.6642 | 0.6798 | 0.9176 | 0.7810 | 0.6200 | 0.7272 | 0.8762 | 0.2202 | 0.0250 |
| SGD logistic regression | **0.7075** | **0.7180** | 0.9086 | **0.8021** | **0.7413** | **0.8350** | **0.5648** | **0.1916** | 0.0358 |

Exact confusion matrices:

- Majority: `[[0, 4,947,542], [0, 9,288,983]]`
- Last response: `[[2,049,077, 2,898,465], [2,832,945, 6,456,038]]`
- Historical accuracy: `[[932,470, 4,015,072], [764,951, 8,524,032]]`
- SGD logistic: `[[1,632,552, 3,314,990], [848,982, 8,440,001]]`

The learned model improves accuracy, F1, ROC-AUC, PR-AUC, log loss and Brier score over the three baselines on this validation split. Its recall is slightly below historical-accuracy persistence, and its ECE is higher than the simple prevalence/history baselines. It is therefore a stronger ranking and overall probability-loss result here, but its probabilities are not yet calibrated to the same ECE as those simple baselines. No confidence interval or test-set result is reported.

## Artifacts

- Full metrics and run configuration: `results/reports/ednet_logistic_experiment.json`
- Summary table: `results/tables/ednet_validation_metrics.csv`
- Reliability-bin values: `results/tables/ednet_validation_calibration.csv`
- Baseline definitions: `models/baselines/ednet_baselines.json`
- Test set: reserved and not evaluated.
