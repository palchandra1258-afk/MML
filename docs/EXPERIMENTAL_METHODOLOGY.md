# MCP-RI Experimental Methodology

## Research questions

The experiments preserve the research reference's central question: can heterogeneous evidence support a temporally grounded, concept-grounded and uncertainty-aware state representation that improves representation decisions? The work proceeds through separable studies; success on a component is not claimed as success for the complete loop.

### Study 0 — Data and construct audit

For each candidate dataset, verify current access, licensing/terms, population, modality files, timestamp quality, labels, missingness, learner/session IDs and outcome definitions. Produce a data dictionary and label-to-construct map before training. Stop or revise an experiment if its target is absent. This is a necessary feasibility stage, not an empirical result.

### Study 1 — Observable outcome baseline

On a constrained task dataset such as CMU DataShop if verified, predict a recorded next response outcome from prior interaction history and task metadata. This tests whether a minimal behavioral trajectory model is viable and establishes a non-cognitive baseline. Do not describe correctness prediction as cognitive-state estimation.

### Study 2 — Unimodal vs multimodal evidence

On a synchronized dataset with a common documented target (Math Data Corpus if its schema/access support it; otherwise an appropriate documented MUTLA target), compare each available modality independently with late fusion. Keep target and eligible cohort fixed across comparison. Interpret labels according to their actual construct (e.g. engagement, correctness, representation content).

### Study 3 — Static vs temporal modeling

Compare static window aggregates and previous-observation/persistence baselines with GRU or temporal convolution on repeated sequences. Use participant-held-out and time-aware testing. Only add a temporal transformer if sample size, label density and compute support it.

### Study 4 — Uncertainty and mismatch

Calibrate predictions for existing labeled targets. Separately, if mismatch detection is pursued, define representation mismatch with a protocol and collect independent expert annotations or an appropriate learner measure. Do not use answer errors or retries as automatic mismatch labels. Report annotation agreement and disagreement; consider soft labels or adjudication.

### Study 5 — Representation choice and outcome

Begin with the inspectable rule-based planner and usability/continuity checks. To claim that state-aware representation selection improves learning, conduct a prospective study with prespecified action options, exposure verification, pre/post concept-aligned outcomes and preferably random assignment/ counterbalancing. Existing observational datasets usually cannot identify causal benefit because the chosen action is confounded by learner/context and action availability.

## Baseline-first comparison matrix

| Comparison | Systems | Question answered | Controls |
|---|---|---|---|
| Prior vs learned | Majority/prevalence and last-observation baselines vs logistic regression/GBDT | Is there signal beyond target prevalence or persistence? | Same training/test learners and target |
| Unimodal | Text-only, visual-only, interaction-only (only where present) | What does each available source predict? | Matched eligible cohort, same target |
| Multimodal | Late fusion, then masked concatenation, optional cross-attention | Do combinations add predictive value over the best single modality? | Same cases, modality masks, ablations and confidence intervals |
| Static vs temporal | Current-window aggregates vs event sequence model | Does temporal order/history add value? | Same temporal cutoff, no future-event leakage |
| Mastery-only vs evidence model | Available mastery/previous correctness baseline vs multimodal evidence model | Does richer evidence improve target prediction? | State labels remain target-defined; no unsupported cognitive claims |
| Fixed vs rule-based representation plan | Fixed action vs explicit rules/diagnostic fallback | Can inspectable policy preserve continuity and produce feasible plans? | Process and outcome measures separated |
| Rule-based vs learned policy (future) | Initial planner vs decision model | Does learned policy improve outcomes? | Randomized/valid causal evaluation and action coverage |

## Splits and validation

- **Primary split:** group by learner so all events/windows from one person remain in one partition.
- **Temporal split:** when deployment asks about future sessions, use train-on-earlier/test-on-later design; document whether learners overlap and provide learner-disjoint results where feasible.
- **Nested tuning:** use grouped inner validation for hyperparameters and feature selection; reserve a final test group untouched.
- **Calibration split:** use a separate calibration partition or cross-fitting within training/validation; never calibrate on the final test set.
- **Dataset transfer:** train/test within each dataset first. Cross-dataset transfer is a separate experiment with construct and domain caveats, not a pooled shortcut.
- **Modality missingness:** evaluate complete-case matched comparisons and natural missing-modality performance separately. Do not impute absent modality as a meaningful zero.

## Labels and construct validity

For every target, publish a target definition, source, collection time, unit, annotator/measurement procedure, class balance and known limitations. Keep these constructs distinct:

- correctness/performance;
- affect/engagement annotations;
- explanation or representation-content coding;
- self-reported understanding/confidence;
- expert-coded misconception or representation mismatch;
- post-intervention learning outcome.

No one target is an automatic substitute for another. Self-report is evidence but may be noisy; expert judgment needs documented protocol and agreement. If a dataset lacks a suitable target, use it for unsupervised representation/component analysis only where justified, or do not use it for that supervised claim.

## Metrics

### Classification

Report macro-F1, balanced accuracy, per-class precision/recall and confusion matrix. For binary tasks, include AUROC and preferably AUPRC when imbalance is material. Include log loss and Brier score for probabilistic quality. Accuracy alone is inadequate under class imbalance.

### Regression/ordinal targets

Use MAE/RMSE and rank/ordinal-aware measures as appropriate; specify whether scale distances are meaningful. Do not treat ordinal labels as continuous without justification.

### Calibration and selective prediction

Report reliability plots, Brier score, negative log likelihood and ECE with binning method/sample counts. Evaluate risk/coverage or error among retained predictions as abstention threshold varies. Calibration is target- and distribution-specific.

### Annotation quality

Report inter-rater agreement appropriate to label type (e.g. Cohen/Fleiss kappa or Krippendorff alpha) and prevalence; adjudication protocol. Agreement does not prove construct validity.

### Representation decision and outcomes

Process metrics: plan feasibility, rationale/evidence completeness, continuity/return-point correctness, user override, and action exposure. Outcome metrics: prespecified concept-aligned post-test score or learning gain, with confidence intervals and baseline-adjusted/randomized comparison when design permits. Engagement and usage are secondary outcomes, not learning by definition.

## Uncertainty design

1. Fit the predictor on training data.
2. Select model and hyperparameters with grouped validation.
3. Fit temperature scaling on held-out validation/calibration logits; use isotonic only if calibration sample size and class counts support it.
4. Optionally compare ensembles as epistemic-uncertainty estimates when compute allows; distinguish model uncertainty from label ambiguity and missing-modality uncertainty.
5. Report calibration on a locked test set and, if possible, under dataset/domain shift.
6. Set an abstention/diagnostic-question threshold using validation data and a stated risk/coverage objective. A low-confidence estimate should not trigger a high-impact diversion automatically.

For multiple annotators, retain annotator-level labels and quantify disagreement. If there is no validated uncertainty target, uncertainty concerns model confidence/calibration, not a claim about the learner's subjective uncertainty.

## Statistical reporting

Use learner-level bootstrap or other group-aware confidence intervals. Predeclare primary target, primary metric and comparisons. Limit multiple comparisons or mark exploratory analyses clearly. Report sample and label counts by split, missingness, exclusions, baseline results and failed runs. Do not fill in expected or placeholder scores. No performance result exists until the experiments are run.

## Reproducibility and leakage checklist

- Store split IDs and dataset version/terms.
- Fit normalization, vocabulary, feature selection, imputation, resampling and calibrator on training/validation only as appropriate.
- Do not expose future responses, post-intervention outcomes or test labels in input features.
- Keep participant-derived duplicates and augmented views within the same split.
- Record software/model versions, seeds, hardware and hyperparameters.
- Report data and code access constraints.

## Limitations to acknowledge

Public dataset labels may not represent fine-grained conceptual understanding or representational mismatch. Sensor-heavy datasets may not transfer to a practical system. Dataset sizes can be large in interactions but small in independent learners. Weak construct labels, participant imbalance, missing modalities and domain shift can make deep models appear more useful than they are. Observational action logs do not establish intervention effects. A small controlled study can establish feasibility but may not support broad generalization.
