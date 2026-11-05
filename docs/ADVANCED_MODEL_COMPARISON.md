# Advanced Tabular Model Comparison: EdNet KT1

## Evaluation protocol

The target is whether the next submitted answer matches the official answer key. This is behavioral response correctness, not a direct measurement of understanding or cognitive state. All learned models use the Phase 6 feature whitelist and serialized encoder, deterministic 5% learner sample of the unseen-learner training partition (3,255,537 examples; 27,310 learners), and the same target definition. Every model was scored on the complete unseen-learner validation partition (14,236,525 examples). The test partition was not scored or used for model selection.

Both tree models use sparse matrices. XGBoost's 264,908-example learner-selected validation subset was monitored for early stopping; its best iteration was the configured maximum, so stopping did not activate. Its final metrics, like the Random Forest metrics, use the complete validation partition. Because validation was monitored during fitting, XGBoost validation metrics are development results rather than an independent final estimate. Random Forest configuration and XGBoost parameters are detailed in their experiment reports. Logistic metrics are the existing frozen Phase 6 results.

Consolidated artifacts are [the metrics table](../results/tables/phase7_advanced_comparison_20261104.csv), [calibration bins](../results/tables/phase7_calibration_bins_20261104.csv), [grouped importance table](../results/tables/phase7_feature_importance_20261104.csv), and [reliability diagram](../results/figures/phase7_reliability_20261104.svg). Detailed per-run results remain in each unique `results/reports/phase7-*` directory.

## Validation results

The positive class is correctness (`1`); precision, recall and F1 use a fixed probability threshold of 0.5. PR-AUC is average precision; ECE uses 15 equal-width bins. Lower is better for log loss, Brier and ECE; higher is better for other metrics.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC / AP | Log loss | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Majority/prevalence | 0.652475 | 0.652475 | 1.000000 | 0.789695 | 0.500000 | 0.652475 | 0.645904 | 0.226753 | 0.001133 |
| Last-response persistence | 0.597415 | 0.690153 | 0.695021 | 0.692578 | 0.555617 | 0.679412 | 13.797544 | 0.401311 | 0.399719 |
| Historical-accuracy persistence | 0.664242 | 0.679796 | 0.917650 | 0.781015 | 0.619955 | 0.727247 | 0.876203 | 0.220208 | 0.024962 |
| Phase 6 SGD Logistic | **0.707515** | **0.717993** | 0.908603 | **0.802130** | **0.741321** | **0.835027** | **0.564780** | **0.191647** | 0.035780 |
| Random Forest | 0.652979 | 0.652841 | **0.999813** | 0.789904 | 0.638082 | 0.754314 | 0.628998 | 0.218981 | 0.055175 |
| XGBoost | 0.687650 | 0.695595 | 0.926923 | 0.794768 | 0.690400 | 0.795158 | 0.592577 | 0.203137 | **0.017782** |

The **Phase 6 logistic classifier remains the strongest overall choice** on this validation set: it has the best accuracy, precision, F1, ROC-AUC, average precision, log loss and Brier score. XGBoost has higher recall and the lowest ECE among learned models, but it does not beat logistic regression on the other listed metrics. The Random Forest's recall is almost 1 because it predicts nearly every row as correct; its accuracy remains near the 65.25% class prevalence.

No model wins every metric. The majority baseline's ECE is unusually low because its one constant probability closely matches the validation prevalence; its ROC-AUC is 0.5 and it cannot rank individual responses. ECE alone should not be used to select the model.

## Computation

| Model | Fit time | Whole-run wall time | Peak process RSS |
|---|---:|---:|---:|
| Phase 6 SGD Logistic (3 epochs) | 3,887.3 s | 6,577.0 s | 1,811,420 KiB (~1.73 GiB) |
| Random Forest (24 trees) | 6.2 s | 2,743.9 s | 3,806,796 KiB (~3.63 GiB) |
| XGBoost (300 trees) | 4,138.7 s | 8,005.7 s | 2,783,436 KiB (~2.65 GiB) |

Whole-run time includes scans of the 5.5 GB compressed table, feature transformation, serialization and validation. RF peak RSS includes the complete process and validation probability buffers, not only tree storage. XGBoost reached its maximum 300 rounds; early stopping did not activate. These timings are from this host and should not be treated as hardware-independent benchmarks.

## Feature interpretation

Grouped tree importance is saved per experiment. XGBoost gain is dominated by current question ID and current skill tags (together about 93% of grouped gain). Random Forest impurity importance is more distributed, with current tags, question ID, prior skill-tag correctness, prior correct count and prior answered attempts highest. Current item identity being important is compatible with item difficulty/selection structure in the data, but the experiment cannot distinguish those mechanisms. These importances are not causal explanations, and high-cardinality categories, correlated history features, and model configuration affect them.

## Recommendation and limits

Keep Phase 6 logistic regression as the primary benchmark for subsequent research. It outperformed both nonlinear models on most predictive metrics and has better Brier/log loss than both. XGBoost may merit a targeted follow-up only if its lower ECE or recall is important to the application and its compute cost is acceptable; that follow-up should predeclare which validation objective is being optimized. The selected tree configurations are initial comparisons, not exhaustive hyperparameter searches. No confidence intervals, learner-clustered uncertainty, or test-set results are claimed. The two tree runs use separate unique experiment IDs and preserve their artifacts.
