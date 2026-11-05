# First Logistic Regression Experiment: EdNet KT1

## Model choice

The experiment used `sklearn.linear_model.SGDClassifier(loss="log_loss")`, which fits a logistic classifier incrementally on sparse chunks. A conventional batch `LogisticRegression` fit would require materializing or repeatedly solving against a very large sparse design matrix for 66.9 million training targets. Incremental SGD keeps memory bounded and supports reproducible chunk processing. It remains a classical linear model; no deep learning was used.

## Dataset inspection

The processed source is a 5,888,235,415-byte gzip CSV with 31 columns. CSV cells arrive as strings and are parsed according to the saved schema/feature definition. It has 95,293,926 rows, including 95,266,280 binary targets and 27,646 blank-answer rows with no target. No processed rows were loaded all at once.

On the full unseen-learner training split, the target counts are 43,725,275 correct and 23,172,971 incorrect (65.36% correct). The validation split has 65.25% correct. The majority baseline therefore predicts the positive class for all examples; other metrics are necessary.

## Training subset and transformations

- **Training sample:** 3,255,537 labelled examples from 27,310 learners, selected as 5% of unseen-learner training learners by deterministic BLAKE2 hash with seed `2025`. All target examples for a selected learner stay in the sample; validation/test learners cannot enter it.
- **Validation:** all 14,236,525 targets in the unseen-learner validation partition.
- **Test:** not evaluated.
- **Epochs:** 3; batch size 20,000.
- **SGD:** logistic loss, L2 `alpha=1e-5`, `learning_rate="optimal"`, averaged weights, seed `2025`, no class weights or resampling.
- **Categorical encoding:** training-sample vocabularies for current question ID, part, and individual skill tags; one-hot encoded as a CSR sparse matrix with fixed unknown/missing buckets. Fit-sample cardinalities were 12,179 question IDs, 7 parts, and 188 skill tags. The full encoded feature dimension was 12,404, including categorical columns, numeric columns, and missing indicators.
- **Numeric transformation:** count/time values use `log1p`; train-sample means and standard deviations are fitted only on sampled training rows. Missing values are mean-imputed (scaled value zero) with explicit missing indicators. The same stored encoder is used for validation.
- **Excluded whitelist field:** `previous_response_skill_tags` is a high-cardinality tag-combination string and is redundant with current-tag conditioning and prior per-skill summaries. All features used are members of the documented preprocessing feature whitelist.

Input fields exclude the target row's submitted answer, answer key, correctness, elapsed duration, learner identifier, timestamp, split labels, and provenance fields. The target is correctness from the official key join. No feature uses a future response.

## Training resources and artifacts

- Scikit-learn: 1.9.1; dependency declaration: `requirements-training.txt`.
- Training time for three passes: 3,887.3 seconds (~64.8 minutes).
- Encoder fit time: 1,255.0 seconds.
- Validation scoring time: 1,434.6 seconds.
- Total run time: 6,577.0 seconds (~109.6 minutes).
- Peak process RSS: 1,811,420 KiB (~1.73 GiB).
- Model: `models/trained/ednet_sgd_logistic.joblib`.
- Encoder/vocabulary/scaler: `models/preprocessing/ednet_sgd_preprocessor.json`.
- Baseline specifications: `models/baselines/ednet_baselines.json`.

The model is sample-trained, not full-training-split-trained. Its validation metrics must be interpreted as the result of the stated 5%-of-training-learners procedure. No test metrics, confidence intervals, or calibrated post-hoc model are included.
