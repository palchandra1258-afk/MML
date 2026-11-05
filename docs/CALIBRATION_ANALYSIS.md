# Calibration Analysis: EdNet KT1 Phase 7

## Protocol

Calibration is assessed for the behavioral next-response correctness probability on the complete unseen-learner validation partition (14,236,525 examples). Probabilities are binned into 15 equal-width bins over [0, 1]. Expected calibration error (ECE) is the example-weighted absolute difference between mean predicted probability and observed correctness rate per occupied bin. Brier score and log loss are also reported because ECE depends on binning and is not a proper scoring rule.

No post-hoc calibration or probability transformation was fitted. The validation learner subset used for XGBoost early stopping chose the iteration only; all reported calibration metrics below use the complete validation partition. The test partition was not evaluated.

## Results

| Model | Log loss | Brier score | ECE (15 bins) |
|---|---:|---:|---:|
| Majority/prevalence | 0.645904 | 0.226753 | 0.001133 |
| Last-response persistence | 13.797544 | 0.401311 | 0.399719 |
| Historical-accuracy persistence | 0.876203 | 0.220208 | 0.024962 |
| Phase 6 SGD Logistic | **0.564780** | **0.191647** | 0.035780 |
| Phase 7 Random Forest | 0.628998 | 0.218981 | 0.055175 |
| Phase 7 XGBoost | 0.592577 | 0.203137 | **0.017782** |

Lower values are better for all three metrics. Logistic regression has better log loss and Brier score than both tree models. XGBoost has lower ECE than the other learned models; the Random Forest has higher ECE than logistic regression. Historical-accuracy persistence also has lower ECE than logistic regression, while its log loss is much worse. The prevalence baseline's ECE is tiny because its constant probability is close to the validation prevalence; this does not make its ranking useful (ROC-AUC is 0.5). The hard last-response probabilities are extremely overconfident when wrong, producing very poor log loss, Brier score, and ECE.

Thus, calibration conclusions depend on the chosen metric. XGBoost has closer average binwise calibration under this 15-bin ECE measure, but it does not dominate proper scoring rules. No model should be described as generally or fully calibrated from these results. The calibration-bin CSV is retained with the experiment artifacts for reliability plots and inspection.

## Limitations

- ECE depends on the number and placement of bins; empty bins contribute no direct error.
- Validation observations are repeated interactions from different learners, so row-wise uncertainty would overstate effective sample size. Learner-clustered uncertainty is not yet estimated.
- The validation set represents unseen learners under the fixed split. Calibration may differ under temporal-known-learner prediction or another dataset.
- XGBoost monitored a learner-selected validation subset during fitting (the round cap was reached); final calibration results used all validation examples, but no separate calibration set was reserved for post-hoc fitting.
- The held-out test partition remains untouched.
