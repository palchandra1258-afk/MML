# Phase 8 Sequence Model Comparison

**Run:** `phase8-temporal-20261105T073420Z-seed2025`

**Evaluation cohort:** 11,382,220 matched transitions from 90,982 unseen validation learners.

**Positive class:** next submitted answer is correct. Classification threshold: 0.5. No test labels were used or evaluated.

## Raw report-only validation metrics

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC / AP | Log loss | Brier | ECE (15 equal-width bins) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Majority | 0.653616 | 0.653616 | 1.000000 | 0.790529 | 0.500000 | 0.653616 | 0.645180 | 0.226402 | 0.000007 |
| Last response | 0.598213 | 0.692255 | 0.693650 | 0.692952 | 0.555887 | 0.680418 | 13.877408 | 0.401787 | 0.401787 |
| Historical accuracy | 0.665885 | 0.681647 | 0.917171 | 0.782061 | 0.622113 | 0.729399 | 0.874932 | 0.219513 | 0.025098 |
| SGD Logistic | 0.708493 | 0.719093 | 0.909166 | **0.803036** | 0.742434 | 0.836592 | 0.563414 | 0.191093 | 0.036098 |
| Random Forest | 0.654117 | 0.653981 | 0.999811 | 0.790737 | 0.638896 | 0.755852 | 0.628278 | 0.218638 | 0.056320 |
| XGBoost 600 | 0.693998 | 0.702070 | 0.923895 | 0.797851 | 0.701016 | 0.803360 | 0.585884 | 0.200223 | 0.019733 |
| DKT | 0.711004 | 0.732101 | 0.879796 | 0.799182 | 0.740994 | 0.837646 | 0.558490 | 0.189447 | **0.006241** |
| SAKT-style | **0.713321** | **0.744860** | 0.853877 | 0.795652 | **0.746430** | **0.841102** | **0.555102** | **0.187996** | 0.013177 |

Raw counts and temperature-scaled metrics for all eight comparators are in [`validation_metrics.csv`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/validation_metrics.csv). The cohort was matched by scoring the existing Phase 6–7 models on exactly the sequence-model report rows. Every learner's first response was excluded because no earlier response is available to a sequence model.

## Interpretation

SAKT has the strongest pooled accuracy, precision, ROC-AUC, average precision, log loss, and Brier score. Logistic has the strongest F1 at the fixed 0.5 threshold. DKT has lower accuracy than SAKT, slightly lower ROC-AUC than logistic, but better pooled log loss and Brier score than logistic. The Random Forest nearly predicts the positive class for every row, so its high recall and F1 do not make it a strong ranking model.

Relative to logistic on this matched cohort, SAKT changes the pooled metrics by +0.004828 accuracy, +0.003997 ROC-AUC, +0.004510 AP, -0.008312 log loss, -0.003096 Brier, -0.007384 F1, and -0.022921 ECE. DKT changes them by +0.002511 accuracy, -0.001440 ROC-AUC, +0.001054 AP, -0.004924 log loss, -0.001646 Brier, -0.003854 F1, and -0.029856 ECE. Lower log loss, Brier, and ECE are better.

This comparison holds the target, learner partitions, report rows, and evaluation code constant, but **does not isolate architecture alone**: logistic regression uses the existing engineered tabular feature vector (including item/skill and aggregate-history fields), while DKT and SAKT use question IDs and prior response correctness sequences only. The measured difference is between model-and-input pipelines. A controlled architecture ablation would need feature-equivalent baselines.

The pooled-row result is not the same estimand as an average over learners. A 1,000-resample paired bootstrap of learner-level mean metrics gives:

| Sequence model minus logistic | Mean per-learner difference | 95% learner-bootstrap percentile interval |
|---|---:|---:|
| DKT log loss | -0.016926 | [-0.018078, -0.015832] |
| DKT Brier | -0.004474 | [-0.004893, -0.004078] |
| DKT accuracy | -0.007988 | [-0.009326, -0.006596] |
| SAKT log loss | -0.021853 | [-0.022830, -0.020838] |
| SAKT Brier | -0.006983 | [-0.007403, -0.006596] |
| SAKT accuracy | +0.000565 | [-0.000623, +0.001858] |

Negative log-loss/Brier differences favor the sequence model; for accuracy, positive favors the sequence model. Thus both sequence models have lower average per-learner probability error, but neither has a demonstrated learner-macro accuracy gain over logistic; DKT's learner-macro accuracy is lower. The bootstrap resamples learners and is conditional on this single trained run; it does not account for training-seed or training-sample variation.

## Published-paper context

The SAINT+ EdNet paper reports DKT 0.7060 accuracy / 0.7638 AUC, SAKT 0.7073 / 0.7663, SAINT 0.7178 / 0.7816, and SAINT+ 0.7252 / 0.7914. It used an updated EdNet snapshot with 60,294,498 interactions and 678,128 learners, held out the most recent 100K students for test, trained on 80% of the remaining data, and used test-set model selection/evaluation as described in the paper. This project used only a deterministic 5% sample of the preexisting training learner partition and evaluates a report-only subset of its separate unseen-learner validation partition. The SAKT implementation and model scale also differ. These figures are useful context, not a matched benchmark: this experiment does not show that MCP-RI equals or exceeds the paper's result ([SAINT+ paper](https://arxiv.org/html/2010.12042)).

## Recommendation

Retain logistic as a strong, interpretable baseline and SAKT as the best candidate for a follow-up EdNet sequence-model study. Do not select SAKT solely by pooled accuracy: its F1 is lower, and the learner-macro accuracy interval includes zero. Before looking at test labels, specify the intended estimand (row-weighted or learner-weighted), primary metric, expanded training scale, tuning budget, and calibration procedure. Retrain all comparison baselines under that same expanded protocol before making paper-level performance claims.
