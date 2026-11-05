# EdNet KT1 XGBoost Experiment

## Objective and protocol

This experiment predicts whether the current submitted answer is correct. It is a behavioral response outcome, not a direct measurement of understanding or cognitive state. It uses the same processed EdNet KT1 data, feature whitelist, serialized training-only encoder, target, deterministic 5% training-learner sample, and unseen-learner protocol as Phase 6. It does not read or score the test partition.

The training sample contains 3,255,537 examples from 27,310 learners. The complete validation partition contains 14,236,525 examples. The sparse training matrix has 12,404 columns and 56,538,805 nonzeros. Training and validation features were transformed in chunks; no dense matrix was created.

## Configuration

`xgboost.XGBClassifier` used `tree_method="hist"`, 300 maximum boosting rounds, learning rate 0.05, maximum depth 6, row subsampling 0.8, column subsampling 0.8, L2 regularization 5, `min_child_weight=10`, and `max_bin=128`. L1 regularization was 0; `scale_pos_weight=1` and no sample weights were used. Eight CPU workers were configured. The input was CSR sparse.

Early stopping monitored validation log loss for 20 rounds on a deterministic validation-learner subset of 264,908 examples (about 2% of validation learners). The complete validation partition was used for final metrics. The best iteration was 299, equal to the configured maximum, so early stopping did not activate; a larger round cap may be considered in a later, explicitly versioned experiment. The validation subset was monitored during fitting, so these are development-validation metrics rather than an independent final estimate. The separate test partition remains untouched for a later frozen evaluation.

XGBoost 3.1.3 was installed in the temporary environment `/tmp/mcp-ri-ml-env`; `requirements-training.txt` pins this version for reproducibility. The [official XGBoost sklearn-estimator documentation](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html) describes the estimator interface and validation-set early stopping.

## Full validation results

Correctness (`1`) is the positive class. The fixed probability decision threshold is 0.5. PR-AUC is average precision; ECE uses 15 equal-width bins.

| Metric | XGBoost | Phase 6 SGD Logistic |
|---|---:|---:|
| Accuracy | 0.687650 | 0.707515 |
| Precision | 0.695595 | 0.717993 |
| Recall | 0.926923 | 0.908603 |
| F1 | 0.794768 | 0.802130 |
| ROC-AUC | 0.690400 | 0.741321 |
| PR-AUC / AP | 0.795158 | 0.835027 |
| Log loss | 0.592577 | 0.564780 |
| Brier score | 0.203137 | 0.191647 |
| ECE | 0.017782 | 0.035780 |

XGBoost has higher recall and lower ECE than logistic regression, but lower accuracy, precision, F1, ROC-AUC, average precision, and worse log loss and Brier score. It did not improve overall predictive performance under the fixed protocol. Its lower ECE is a limited calibration advantage on this validation set, not proof of calibration across populations or protocols.

## Runtime and artifacts

- Fit time: 4,138.7 seconds (about 69 minutes).
- Complete experiment wall time: 8,005.7 seconds (about 133 minutes, including data scans and validation scoring).
- Peak process RSS: 2,783,436 KiB (about 2.65 GiB).
- Model: `models/trained/xgboost/phase7-20261104T100506Z-seed2025/model.json`.
- Grouped gain importance: `models/trained/xgboost/phase7-20261104T100506Z-seed2025/grouped_gain_importance.json`.
- Metrics, calibration bins, experiment configuration, and run metadata: `results/reports/phase7-20261104T100506Z-seed2025/`.

Feature importance is grouped by original feature field, summing the gain of its one-hot/numeric columns. Current question ID and current skill tags dominate the reported gain. Gain is model split usage, not a causal effect or a measure of educational importance. High-cardinality categorical fields have more candidate split columns and can accumulate more importance. Importance does not establish that current item metadata would be available in a different prediction setting.

This initial tree model is computationally expensive and did not beat the simpler logistic model on most metrics. The result supports keeping the logistic model as the primary reference unless a later, predeclared experiment demonstrates a reliable gain.
