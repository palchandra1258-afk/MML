# Continued XGBoost Training: EdNet KT1

## Purpose and safeguards

This run resumes the Phase 7 XGBoost checkpoint after the original run reached its 300-round cap without early stopping. It tests whether additional boosting improves the same behavioral next-response correctness task. It is not cognitive-state prediction.

The run reused the identical 5% deterministic training-learner sample (3,255,537 examples from 27,310 learners), target, 12,404-column sparse feature representation, fitted Phase 6 encoder, and unseen-learner protocol. No features or class weights were added. The test partition was not read. XGBoost monitored a deterministic validation-learner subset for early stopping, and reported metrics were scored on the full 14,236,525-example validation partition. Since validation guided continuation, these are development-validation results; the test split remains reserved for a later frozen evaluation.

## Continuation configuration

The saved 300-round booster was continued for up to 300 additional rounds (XGBoost 3.1.3), with validation log-loss patience of 30 rounds. Other settings were held at learning rate 0.05, depth 6, row and column subsampling 0.8, L2 5, L1 0, `min_child_weight=10`, `scale_pos_weight=1`, histogram trees with 128 bins, seed 2025, and eight workers. The 264,908-example early-stopping subset contained 2,310 validation learners.

The model reached **600 total rounds** and `best_iteration=599`; early stopping again did not activate. It used the entire configured continuation block rather than an earlier stopping point.

## Validation results

Correctness is the positive class; hard predictions use threshold 0.5. PR-AUC is average precision; ECE uses 15 equal-width bins.

| Metric | Resumed XGBoost (600 rounds) | Original XGBoost (300 rounds) | Phase 6 SGD Logistic |
|---|---:|---:|---:|
| Accuracy | 0.692517 | 0.687650 | **0.707515** |
| Precision | 0.700369 | 0.695595 | **0.717993** |
| Recall | 0.924086 | **0.926923** | 0.908603 |
| F1 | 0.796822 | 0.794768 | **0.802130** |
| ROC-AUC | 0.699911 | 0.690400 | **0.741321** |
| PR-AUC / AP | 0.801781 | 0.795158 | **0.835027** |
| Log loss | 0.587215 | 0.592577 | **0.564780** |
| Brier score | 0.200807 | 0.203137 | **0.191647** |
| ECE | 0.019764 | **0.017782** | 0.035780 |

Adding 300 rounds improved XGBoost accuracy, precision, F1, ROC-AUC, average precision, log loss, and Brier score relative to its original checkpoint. Recall decreased slightly and ECE increased slightly. Logistic regression still leads on accuracy, precision, F1, ranking, log loss, and Brier score; resumed XGBoost has higher recall and lower ECE. The extra rounds do not change the recommendation to retain logistic regression as the primary model.

## Resource use and artifacts

- Sparse training matrix: 3,255,537 × 12,404, with 56,538,805 nonzeros.
- Matrix construction from one full sequential table scan: 1,377.9 seconds.
- Continuation fit: 4,364.4 seconds (about 72.7 minutes).
- Full validation scoring: 1,557.8 seconds.
- Total wall time: 7,442.3 seconds (about 124 minutes).
- Peak process RSS: 2,741,368 KiB (about 2.61 GiB).
- Model: `models/trained/xgboost/phase7-xgb-resume-20261105T040130Z-seed2025/model.json`.
- Grouped gain importance: `models/trained/xgboost/phase7-xgb-resume-20261105T040130Z-seed2025/grouped_gain_importance.json`.
- Run report, metrics, and calibration bins: `results/reports/phase7-xgb-resume-20261105T040130Z-seed2025/`.

The continued model's grouped gain is dominated by current question ID (77.94%) and current skill tags (18.16%). Gain describes tree split usage, not causal contribution; feature cardinality and correlated inputs affect this distribution.
