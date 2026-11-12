# Phase 9 — Learner State Experiments and Evaluation

## Experiment plan

The reproducible script scans `data/processed/ednet/ednet_kt1_features.csv.gz` once and selects only the existing `split_unseen_learner=validation` partition. It emits one JSON state for each validation learner and an aggregate report. It does not materialize the table or load model artifacts. No cognitive ground truth is available, so the evaluation checks state construction and descriptive behavior rather than cognitive-state classification accuracy.

| Experiment | Question | Reported summaries |
|---|---|---|
| A. Historical state | What full labeled response history was observed for each validation learner and skill? | Learner/concept counts, historical accuracy distribution summaries, evidence tiers. |
| B. Recent state | Does the recent window differ from full-history accuracy? | Number with both estimates and mean absolute recent-to-historical difference. |
| C. Smoothed state | How strongly does the Beta(1,1) prior shrink raw accuracy, especially with little evidence? | Mean absolute shrinkage overall/per concept; concept counts in evidence buckets. |
| D. Temporal change | How often does the explicit latest-five versus preceding-five rule indicate improving/declining/stable performance? | Trend counts; not interpreted as a validated learning trajectory or causal effect. |
| E. Evidence sufficiency | How much evidence supports learner and concept summaries? | Evidence/confidence/uncertainty counts and Wilson interval summaries encoded per state. |

Additional internal checks include schema validation for every state, finite bounded rates, count reconciliation, source chronology, missing-tag/unlabeled handling, duplicate accounting and deterministic small-sequence tests. Unit tests replay prefixes to verify historical reconstruction and that appending future events does not alter a previously generated snapshot.

## Prediction calibration

Not run. The report files contain aggregate validation metrics, but no per-row Phase 6–8 predictions are stored as a reusable inference table. The audit interpreter lacks `joblib`, scikit-learn, XGBoost and PyTorch, and no model loading was successful. Therefore the module records `model_predictions.next_response_correctness=null`. No calibration metrics or model estimates are fabricated. Even a valid calibration curve for response correctness would not establish calibration for understanding or skill mastery.

## Interpretation boundary

These experiments establish whether the code can construct consistent chronological behavioral summaries and how those summaries behave under the specified arithmetic/smoothing rules. They cannot evaluate accuracy against true cognitive state, because the dataset has no direct labels for understanding, confusion, misconception, representation mismatch or intervention response. A future construct-valid evaluation needs independently collected state annotations or validated measures and a participant-held-out protocol.
