# Phase 8 Calibration Analysis

**Run:** `phase8-temporal-20261105T073420Z-seed2025`

**Calibration cohort:** 1,324,710 next-response transitions from 11,728 learners, disjoint from early stopping and report-only evaluation.

**Report-only cohort:** 11,382,220 transitions from 90,982 learners. No test labels were used or evaluated.

## Method

For each comparator, a single positive temperature was fitted by minimizing binary log loss on the calibration learners. It transforms a predicted probability (p) as `sigmoid(logit(p) / T)`. `T > 1` softens extreme probabilities; `T < 1` sharpens them. The fitted scalar was then applied without refitting to report-only predictions. Calibration did not change the 0.5 classification decisions, so accuracy, precision, recall, F1, ROC-AUC, and average precision are unchanged apart from numerical rounding.

ECE is the 15-bin equal-width expected calibration error implemented in the existing metrics helper. ECE depends on binning and cohort prevalence; it is reported beside log loss and Brier score, not treated as a stand-alone model-selection criterion.

## Report-only results before and after temperature scaling

| Model | Temperature | Log loss raw → scaled | Brier raw → scaled | ECE raw → scaled |
|---|---:|---:|---:|---:|
| Majority | 1.0142 | 0.645180 → 0.645189 | 0.226402 → 0.226406 | 0.000007 → 0.002020 |
| Last response | 19.9999 | 13.877408 → 0.683801 | 0.401787 → 0.244968 | 0.401787 → 0.102134 |
| Historical accuracy | 4.2365 | 0.874932 → 0.675292 | 0.219513 → 0.237189 | 0.025098 → 0.130485 |
| SGD Logistic | 1.1173 | 0.563414 → 0.562091 | 0.191093 → 0.190508 | 0.036098 → 0.029196 |
| Random Forest | 0.9019 | 0.628278 → 0.627660 | 0.218638 → 0.218455 | 0.056320 → 0.042855 |
| XGBoost 600 | 0.8895 | 0.585884 → 0.585101 | 0.200223 → 0.200005 | 0.019733 → 0.015911 |
| DKT | 1.0375 | 0.558490 → 0.558372 | 0.189447 → 0.189427 | 0.006241 → 0.003650 |
| SAKT-style | 1.0645 | 0.555102 → 0.554774 | 0.187996 → 0.187908 | 0.013177 → 0.009034 |

The model-level calibration-bin data are in [`validation_calibration_bins.csv`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/validation_calibration_bins.csv), and the SVG gives the raw report-only curves for logistic, DKT, and SAKT ([reliability diagram](../results/figures/phase8-temporal-20261105T073420Z-seed2025_reliability.svg)). Full metrics are in [`validation_metrics.csv`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/validation_metrics.csv).

## Findings and limits

- DKT and SAKT begin with comparatively low report-only ECE; scalar temperature scaling improves their ECE and slightly improves both log loss and Brier score.
- Logistic regression also improves modestly after scaling. On this cohort, SAKT retains the best pooled log loss and Brier score among the learned models after calibration.
- Last-response persistence assigns near-zero/near-one probabilities; the very high raw log loss reflects these overconfident errors. Temperature scaling makes it less extreme, but it remains a weak probability model.
- Historical-accuracy persistence already has a modest raw ECE, but the fitted temperature worsens its report-only ECE and Brier score. This is a useful reminder that a calibration transform optimized for log loss does not necessarily improve every calibration metric.
- The majority baseline has near-zero raw ECE because its constant probability is close to this cohort's outcome prevalence. That does not imply useful individual ranking; its ROC-AUC is 0.5.
- The report-only scores are a held-out validation report cohort, not an independent test result. A single scalar temperature does not provide epistemic uncertainty, subgroup guarantees, or robustness to future data shift. Calibration in this TOEIC/EdNet response cohort does not validate cognitive-state confidence.

Temperature scaling was selected using a separate learner group, so the report-only labels did not fit the temperature. Before any test evaluation, freeze the model, calibration procedure, metrics, and thresholding policy. Preserve calibration monitoring under distribution shift.
