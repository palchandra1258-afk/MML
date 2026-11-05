# Model Evaluation Report: EdNet KT1 Baselines

## Evaluation protocol

This report evaluates a behavioral correctness predictor on the unseen-learner validation split only. There are 14,236,525 validation examples: 9,288,983 correct and 4,947,542 incorrect. The model was trained on a deterministic 5% learner-level sample of the training partition (3,255,537 examples from 27,310 learners). All validation rows were evaluated. The test partition was not read for metrics, used for tuning, or used for model selection.

The training split has 66,898,246 targets (65.36% correct). No class weighting or resampling was used. The majority baseline's 65.25% validation accuracy illustrates why accuracy alone is not an adequate comparison.

## Results

| Model | Accuracy | Precision (correct) | Recall (correct) | F1 (correct) | ROC-AUC | PR-AUC (AP) | Log loss | Brier | ECE, 15 equal-width bins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Majority/prevalence | 0.6525 | 0.6525 | 1.0000 | 0.7897 | 0.5000 | 0.6525 | 0.6459 | 0.2268 | 0.0011 |
| Last-response persistence | 0.5974 | 0.6902 | 0.6950 | 0.6926 | 0.5556 | 0.6794 | 13.7975 | 0.4013 | 0.3997 |
| Historical-accuracy persistence | 0.6642 | 0.6798 | 0.9176 | 0.7810 | 0.6200 | 0.7272 | 0.8762 | 0.2202 | 0.0250 |
| SGD logistic regression | **0.7075** | **0.7180** | 0.9086 | **0.8021** | **0.7413** | **0.8350** | **0.5648** | **0.1916** | 0.0358 |

Confusion matrices use `[[TN, FP], [FN, TP]]`:

- Majority: `[[0, 4,947,542], [0, 9,288,983]]`
- Last response: `[[2,049,077, 2,898,465], [2,832,945, 6,456,038]]`
- Historical accuracy: `[[932,470, 4,015,072], [764,951, 8,524,032]]`
- SGD logistic: `[[1,632,552, 3,314,990], [848,982, 8,440,001]]`

The 0.5 decision threshold was fixed for all methods; no validation threshold search was performed. Persistence probabilities use the prior response or prior accuracy, with full-training prevalence for cold start. ECE is equal-width with 15 bins. The hard last-response probabilities of zero/one are intentionally uncalibrated, which explains its poor log loss and ECE.

## Interpretation

On this validation set, SGD logistic regression outperforms the majority, last-response, and historical-accuracy baselines in accuracy, F1, ROC-AUC, average precision, log loss, and Brier score. Historical accuracy has slightly higher recall (0.9176 versus 0.9086), while the logistic model has higher precision. The model's ECE (0.0358) is worse than the majority baseline (0.0011) and historical-accuracy baseline (0.0250); the probabilities should not be described as fully calibrated. No post-hoc calibration was fit.

This supports a useful baseline signal beyond simple prevalence/history for the stated behavioral task, but it does not demonstrate cognitive-state measurement, representation mismatch detection, or learning benefit. These results also come from a sampled training set and one learner-disjoint validation split; they do not establish full-training-data or temporal-known-learner performance.

## Limitations and next steps

- Train on a larger or full learner-disjoint training partition and compare against the present sample result before treating this as a final model.
- Assess calibration on a separate validation/calibration procedure; do not fit calibration on test data.
- Report learner-grouped confidence intervals and subgroup/sequence-length checks in a follow-up.
- Run the future-known-learner temporal protocol separately; do not combine its results with this experiment.
- Preserve the exact-duplicate policy and consider a declared sensitivity run.
- Evaluate the held-out test set only after model and analysis choices are frozen.

Detailed raw metrics, timing, memory, category cardinalities, and artifacts are in `results/reports/ednet_logistic_experiment.json`, `results/tables/ednet_validation_metrics.csv`, and `results/tables/ednet_validation_calibration.csv`.
