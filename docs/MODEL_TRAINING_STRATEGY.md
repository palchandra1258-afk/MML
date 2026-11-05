# MCP-RI Model Training Strategy

## Principles

1. Training and experimental evaluation are explicit research activities, not implied by running pretrained inference.
2. Train against an observed, defined target. Correctness, pauses, retries and answer changes are not confusion labels.
3. Establish a simple baseline before temporal or deep architectures.
4. Use participant-held-out and, where useful, time-forward splits. Avoid leakage through windows or repeated sessions.
5. Compare modalities only where the dataset supplies them. Report eligible cohorts and missing-modality patterns.
6. Do not create synthetic cognitive labels by renaming behavior proxies.
7. Freeze the test set and use it once for final evaluation. Report uncertainty and calibration, not only accuracy.

## Model/component plan

| Model/component | Research purpose | Input features | Target variable | Dataset requirement | Architecture/algorithm | Training approach | Loss function, where applicable | Evaluation metrics | Expected output |
|---|---|---|---|---|---|---|---|---|---|
| Pretrained ASR (inference only) | Convert available speech to a text evidence stream | Audio segments, timestamps, language if known | None for this project; reference transcript only for ASR evaluation | Dataset with permitted audio; Math Data Corpus/MUTLA/SOPHIAS only if actual audio access is verified | Frozen pretrained speech recognition model | No MCP-RI training; inference only. Record model/version and confidence | None | WER/CER only if human reference transcripts exist; downstream target metrics are separate | Transcript and ASR confidence/timing, marked machine-generated |
| Text feature baseline | Establish whether language features predict a defined observed target | Transcript/text, optional TF-IDF n-grams or frozen embedding | Dataset-provided/human-coded target such as representation-content class or a clearly defined response outcome | Math Data Corpus if text/transcripts and target available; otherwise a separately labeled study | TF-IDF + logistic regression; frozen sentence encoder as comparison | Train classifier on training split; encoder remains frozen | Cross-entropy for classification; regularization | Macro-F1, balanced accuracy, AUROC (binary), log loss/Brier, calibration | Target-specific probabilities; not generic cognitive state |
| Visual artifact feature baseline | Evaluate visual evidence on supported artifacts | Image/diagram/handwriting features; optional OCR; artifact quality | Dataset-provided representation-content/correctness label or new independently annotated target | Math Data Corpus if artifact and documented target available; possibly DAiSEE for its affect target only | Human-coded/engineered baseline, frozen pretrained vision encoder + linear head | Frozen encoder; train only downstream head | Cross-entropy for classes; MSE/ordinal loss only for justified numeric/ordered target | Macro-F1, balanced accuracy, AUROC, annotator agreement, calibration | Artifact category/target probabilities with provenance |
| Interaction-only static baseline | Measure predictive value in behavioral events without diagnosing cognition | Event counts/rates/transitions, prior responses, item/KC metadata if present, elapsed times | Next response correctness or another recorded valid outcome | CMU DataShop equation-solving records or EdNet/OULAD, contingent on field/schema audit | Majority/prior, logistic regression, gradient-boosted trees | Train on training learners; tune within grouped validation | Binary/multiclass cross-entropy; GBDT objective | AUROC, macro-F1, balanced accuracy, Brier/log loss; calibration | Prediction of the exact next-outcome target |
| Interaction temporal model | Test whether sequence/history adds value over static summaries | Ordered event embeddings/features, timestamps, prior observed outcomes | Next response outcome or documented longitudinal label | EdNet/OULAD or CMU DataShop with sufficient sequence history and valid target | Persistence/last-value baseline, then GRU or temporal convolution | Supervised training; learner-held-out and time-forward evaluation | Cross-entropy; masking for variable sequence length | Same metrics as static model plus calibration and subgroup/sequence-length analysis | Future observed outcome probabilities; not inferred confusion |
| Single-modality state-task heads | Establish unimodal reference points for a valid annotation | Text-only, visual-only, or interaction-only features | A specific human annotation, self-report, affect label, content label or performance target; name construct explicitly | Dataset with target-specific labels: e.g. DAiSEE for its affect classes, MUTLA for documented annotations, Math Data Corpus for its actual codes | Logistic/linear model or GBDT; deep modality encoder only if justified | Supervised training; no proxy-label substitution | Cross-entropy or target-appropriate loss | Macro-F1, balanced accuracy, AUROC, calibration, annotator agreement | Probabilities for the named construct only |
| Late-fusion multimodal model | Test whether available modalities provide complementary signal over unimodal systems | Per-modality outputs/features + modality masks and quality features | Same target and same eligible cases as unimodal comparisons | A synchronized dataset with at least two actually observed modalities and a common valid target; Math Data Corpus/MUTLA/ES-KT-24 after schema validation | Weighted/stacked late fusion; logistic regression or GBDT; masked concatenation as secondary | Train fusion head on training partition; group splits maintained | Cross-entropy | Macro-F1, AUROC, Brier/ECE, confidence intervals, missing-modality robustness | Fused target probabilities and modality availability metadata |
| Cross-attention / multimodal deep model (optional) | Test whether learned cross-modal interactions beat simpler fusion | Aligned sequence/token/visual/event representations with masks | Same valid target as fusion baseline | Large enough synchronized and labeled cohort; likely purpose-built or suitable verified corpus | Cross-attention or multimodal transformer | Fine-tune/project modalities only after baseline and power/volume review | Cross-entropy; regularization; modality dropout if justified | Same matched metrics, calibration, subgroup and ablation analysis | Target-specific prediction; higher complexity is not assumed beneficial |
| Temporal cognitive-state estimator (future research target) | Estimate evolving state rather than isolated target | History of evidence bundles, state history, concept context | Repeated validated state annotations or self-reports aligned to time; no invented states | Purpose-built longitudinal study or verified dataset with repeated suitable labels | Persistence baseline; then GRU/temporal convolution; transformer only if data supports | Supervised sequence training; participant-held-out and temporal split | Cross-entropy or multi-task losses for separately validated targets | Per-target macro-F1/AUROC, Brier/ECE, temporal stability, lead-time, selective risk | State distribution per time point, evidence links, uncertainty, abstention |
| Representation mismatch detector (future) | Detect a defined mismatch between current representation and demonstrated need | Current concept/representation, learner evidence and independent annotations | Operationalized mismatch label from blinded expert coding or protocol-defined measure; not incorrectness alone | New labeled study or a suitable verified dataset with this construct | Logistic/GBDT baseline; later multimodal/temporal model | Train on independent annotations; adjudicate disagreements; grouped splits | Cross-entropy; possibly soft-label cross-entropy for multiple annotators | Macro-F1, precision/recall, AUROC, calibration, inter-rater agreement | Probability of the defined mismatch construct, not a diagnosis |
| Representation policy (initial) | Make next action inspectable and continuity-aware | State estimate/uncertainty, concept, request, current frame/form, available content/actions | None; rules specify action, not learned targets | No training dataset; content/action inventory required | Deterministic policy, constraints and diagnostic fallback | No training | None | Feasibility, rationale completeness, continuity/return-pointer correctness; later outcome evaluation | RepresentationPlan with action and rationale |
| Trainable representation decision model (later) | Learn which available action improves a prespecified outcome in context | Pre-action context/state, available action set, assignment/exposure, outcome features | Potential outcome or prespecified follow-up learning outcome | Prospective randomized/strongly identified study with action coverage, pre/post measures and adequate sample; public datasets generally insufficient as described in reference | Start with supervised ranking/uplift or contextual value model; contextual bandit only when justified | Offline model development; prospective evaluation; propensity-aware if observational | Outcome-specific loss / ranking loss; causal estimator assumptions explicit | Policy value with valid design, confidence intervals, uplift/ATE where identifiable, safety/coverage | Action scores or conservative recommendation with uncertainty |
| Uncertainty and calibration wrapper | Make model confidence meaningful and support abstention | Validation-set logits/probabilities; optionally model ensemble outputs | Same validation targets as base model | Any labeled dataset with learner-disjoint calibration split | Temperature scaling; isotonic only with adequate calibration data; deep ensembles optional | Fit calibrator on validation/calibration set only, never test | NLL/Brier calibration objective as appropriate | ECE with binning details, Brier, NLL, reliability diagrams, selective risk/coverage | Calibrated probabilities and abstain/unknown signal |
| State updater (initial) | Preserve new evidence and update estimates without overwriting history | Prior state version + new events/outcome + model estimate | None initially | Any prototype session with event/outcome records | Event-sourced deterministic update rules | No training | None | Audit consistency, traceability, missingness handling, update latency | New versioned state with observed/inferred/unknown separation |

## A. Pretrained models used without additional training

- ASR for audio transcription, if a candidate dataset actually contains permitted audio and the model's language/task support is suitable.
- Frozen text embeddings for linguistic feature extraction.
- Frozen image/vision/OCR encoders for artifacts that are actually present.
- These are **pretrained inference components**, not MCP-RI training. Record model name/version, preprocessing, inference settings and confidence. Evaluate output quality when references exist. Do not represent their use as fine-tuning or as evidence that the downstream construct is valid.

## B. Models requiring fine-tuning

Fine-tuning is optional and later-stage. Candidate cases: text encoder on a sufficiently labeled explanation/content target; vision encoder on independently annotated artifact categories; multimodal projection/cross-attention layers on synchronized data. Fine-tune only after a frozen-feature baseline, label audit, grouped split, compute/privacy review and evidence that sample size supports it. Fine-tuning the ASR model is not planned.

## C. Models trained by the project

- Classical supervised baseline(s): logistic regression and/or gradient-boosted trees for an observed outcome or valid annotation.
- Temporal model(s): GRU/temporal convolution only after sequence data and grouped evaluation justify it.
- Fusion head: trained only on synchronized cases and a common target.
- Calibration layer: fitted on a held-out calibration partition.
- Future state/mismatch/policy models: only after suitable repeated state annotations, mismatch labels or action-outcome data exist.

Training means fitting parameters on the training partition, documenting objective and splits, then evaluating on untouched held-out learners. A frozen pretrained encoder with a newly fitted classifier is a trained downstream model but not a fine-tuned encoder; report that distinction.

## D. Rule-based components requiring no training

- Event validation, timestamp normalization and feature aggregation.
- Modality availability masks and provenance tracking.
- State schema and observed/inferred/unknown distinctions.
- Initial representation planner and low-confidence diagnostic fallback.
- Branch parent/return pointer and continuity bookkeeping.
- Event-sourced outcome/state update rules.
- Split manifest and experiment metadata checks.

## Dataset requirements and selection gates

1. **First predictive baseline:** audit CMU DataShop equation-solving data (or another verified constrained interaction dataset) for transaction history and a recorded subsequent correctness outcome. The reference describes CMU DataShop as interaction data around equation solving, but exact fields, access and terms still require verification. If its schema lacks the target, use the Math Data Corpus only if its documented correctness/problem labels and access support the same prediction task. Do not manufacture a target.
2. **Multimodal component experiment:** prefer Math Data Corpus if speech, pen/image artifacts, timestamps and a shared documented target are available. MUTLA can support a separate engagement/state-label experiment only for its actual annotations; do not merge its construct with conceptual mismatch.
3. **Content-side resource:** EduMUSE may support concept/figure/content alignment and representation inventory; it is not learner-state training data by itself.
4. **Temporal behavioral comparison:** EdNet/OULAD provide separate behavioral benchmarks as described in the reference, not a proxy for missing multimodality.
5. **Mismatch and decision loop:** likely requires a new, ethically approved study with independently defined labels and post-intervention outcomes. A sample-size/power plan must precede collection.

## Model training location and artifact flow

Training is performed offline in a reproducible research environment, not in the user-facing inference loop. Use CPU for initial classical baselines; use GPU only if a chosen pretrained encoder or fine-tuning experiment requires it. Exact local/cloud placement depends on dataset terms, institutional policy, privacy and compute and is not fixed yet. Training consumes approved versioned splits and writes model weights, preprocessing/calibration artifacts, metrics, logs, dataset/split metadata and checksums. Inference loads immutable artifacts. No online weight updates are planned.

## Baseline-first training sequence

1. Dataset/schema and label audit; freeze target and split unit.
2. Majority/prior baseline and simple feature-only baseline.
3. Logistic regression and gradient-boosted trees on one modality.
4. Compare static history features with a simple temporal model.
5. Add modality-specific systems and late fusion on the same eligible cases.
6. Add deep fusion/fine-tuning only if it has a justified data and compute case.
7. Calibrate selected model on a held-out calibration set; report test-set metrics once.
8. Only after valid state/mismatch labels exist, evaluate state estimation. Only after action/outcome data exist, evaluate trainable representation selection.
