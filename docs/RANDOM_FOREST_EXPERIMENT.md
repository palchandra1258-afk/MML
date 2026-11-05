# EdNet KT1 Random Forest Experiment

## Objective and protocol

This model predicts the correctness of the next submitted answer, a behavioral response outcome. It does not directly measure understanding or cognitive state. The experiment reused the Phase 6 processed EdNet KT1 dataset, feature whitelist and saved encoder, target, 5% deterministic training-learner sample, and unseen-learner split. It trained on 3,255,537 examples from 27,310 learners and scored all 14,236,525 validation examples. The test partition was not used.

The feature matrix was CSR sparse with 12,404 columns and 56,538,805 nonzeros. No dense conversion or additional feature engineering was introduced.

## Initial manageable configuration

The `RandomForestClassifier` used 24 trees, maximum depth 12, minimum leaf size 500, `max_features="sqrt"`, bootstrap sampling with 50% of training rows per tree, no class weighting, seed 2025, and eight workers. The large minimum leaf and shallow tree limit are intended to constrain model size and overfit risk. The forest accepts the shared sparse input through scikit-learn's sparse handling.

## Full validation results

Correctness (`1`) is the positive class; the fixed probability threshold is 0.5. PR-AUC is average precision; ECE uses 15 equal-width bins.

| Metric | Random Forest | Phase 6 SGD Logistic |
|---|---:|---:|
| Accuracy | 0.652979 | 0.707515 |
| Precision | 0.652841 | 0.717993 |
| Recall | 0.999813 | 0.908603 |
| F1 | 0.789904 | 0.802130 |
| ROC-AUC | 0.638082 | 0.741321 |
| PR-AUC / AP | 0.754314 | 0.835027 |
| Log loss | 0.628998 | 0.564780 |
| Brier score | 0.218981 | 0.191647 |
| ECE | 0.055175 | 0.035780 |

The forest nearly predicts every response as correct at the 0.5 cutoff. Its accuracy and F1 are close to the majority baseline, while its ROC-AUC and average precision show ranking signal above prevalence. Logistic regression is better on accuracy, precision, F1, recall is lower, ranking metrics and proper probability scores. The forest's ECE is also worse. Under this configuration, the Random Forest does not replace logistic regression.

## Runtime, memory, artifacts

- Fit time: 6.2 seconds for 24 trees.
- Full experiment wall time: 2,743.9 seconds (about 45.7 minutes), dominated by scanning the 5.5 GB compressed table and full validation prediction.
- Peak process RSS: 3,806,796 KiB (about 3.63 GiB); this is whole-process peak memory, not forest-only memory.
- Model: `models/trained/random_forest/phase7-20261104T121919Z-seed2025/model.joblib`.
- Grouped impurity importance: `models/trained/random_forest/phase7-20261104T121919Z-seed2025/grouped_importance.json`.
- Metrics, calibration bins, configuration and run metadata: `results/reports/phase7-20261104T121919Z-seed2025/`.

## Feature importance caveats

Grouped Random Forest impurity importance assigns the sum of per-column impurity reduction to each source field. Current skill tags, current question ID, prior correct count, and prior skill-tag correct count ranked highest in this run. This is a model-specific association, not causality. Impurity importance can favor high-cardinality fields and can distribute importance unpredictably across correlated summaries. The forest's leaf size, depth, bootstrap and feature-sampling choices also affect the ranking. A permutation analysis on a learner-level validation sample is a possible follow-up, with a defined cost and uncertainty procedure.
