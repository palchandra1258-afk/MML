# MCP-RI Module Specifications

This document defines module responsibilities and contracts for the four research layers. The modules describe a planned system; none is implemented yet. Dataset-specific support and label availability must be verified before enabling a module.

## Shared conventions

- IDs are pseudonymous and stable only within the approved study scope.
- Times use the dataset's documented time base and retain original timestamps plus normalized time when available.
- Every derived feature includes source event IDs, preprocessing version and modality availability/quality.
- Missing data is represented explicitly. It is not imputed as evidence of absence unless a documented method requires imputation.
- All model outputs name their prediction target. A performance prediction is not renamed cognitive state.

## Module 1: Context and Event Ingestion

**Purpose:** validate and normalize source events while preserving provenance.

**Inputs:** dataset records or, in a future study, consented session events; dataset schema; concept/task metadata where supplied.

**Outputs:** validated `ObservationEvent` records and `SessionContext`; quarantine/error records for invalid timestamps or malformed inputs.

**Features:** timestamps/intervals, event type, action type, task/item ID, correctness if recorded, artifact/audio/text references, source quality and missingness.

**Labels:** none. This is data engineering, not a predictor.

**Validation:** schema pass rate, timestamp checks, duplicate/event reconciliation, modality availability summaries, and sample-level provenance audits. No cognitive model metrics apply.

## Module 2: Language and Voice Evidence Encoder

**Purpose:** derive linguistic evidence from text and, only when present, transcribed audio.

**Inputs:** text/transcript and optional raw audio with timestamps, language and consent/access information.

**Outputs:** transcript tokens or text features, ASR confidence/timing when applicable, pretrained text embeddings or transparent lexical features, provenance.

**Candidate approaches:** TF-IDF/word n-gram baseline; frozen pretrained sentence encoder; optional pretrained ASR for audio transcription. Fine-tune a text model only against a valid task-specific label with participant-level splits.

**Labels:** none for frozen feature extraction. A downstream supervised task needs a separately defined target such as a human-coded explanation category or an explicit self-report—not an assumed cognitive label.

**Evaluation:** ASR word error rate only if reference transcripts exist; downstream macro-F1/AUROC or task-appropriate metrics against the defined label; calibration for probabilities. Embedding quality is not itself evidence of cognitive validity.

## Module 3: Visual Artifact Encoder

**Purpose:** represent diagrams, handwriting or other visual artifacts that are actually present in the chosen dataset.

**Inputs:** image/digital-pen artifact, task/context and timestamp. Do not assume every dataset has images or pen traces.

**Outputs:** OCR/transcription if applicable, image embeddings or human-coded features, artifact type/content features and confidence/provenance.

**Candidate approaches:** human-coded category baseline; pretrained OCR/vision model in frozen inference mode; engineered digital-pen sequence features where raw pen events exist. Fine-tune vision only with adequately labeled training artifacts and a defined target.

**Labels:** dataset-provided representational content/correctness only where documented; otherwise a separately annotated artifact target. Image presence does not imply a misconception label.

**Evaluation:** task-specific macro-F1/weighted F1, agreement with independent annotators for coded labels, and AUROC where appropriate. Report inter-rater agreement and label coverage.

## Module 4: Interaction Trajectory Encoder

**Purpose:** encode event sequence and time-dependent behavior as behavioral evidence.

**Inputs:** timestamped attempts, edits, navigation, hints, pauses or other events actually recorded by the dataset.

**Outputs:** windowed counts/rates, event order/transitions, elapsed intervals and sequence embedding; explicit availability mask.

**Candidate approaches:** event-count baseline; logistic regression/gradient-boosted trees; temporal GRU or temporal convolution if the dataset supports enough longitudinal examples. Transformer models are later candidates, not defaults.

**Labels:** predict only recorded/validated targets such as subsequent response correctness or a human annotation. Repeated attempts, pauses and answer changes are not labels for confusion.

**Evaluation:** AUROC, macro-F1, balanced accuracy, log loss/Brier and calibration as appropriate; evaluate learner-held-out and temporal generalization.

## Module 5: Evidence Fusion and Alignment

**Purpose:** combine synchronized, available modality features without hiding missingness or contradictions.

**Inputs:** modality feature records, timestamps/intervals, quality and modality masks.

**Outputs:** aligned `EvidenceBundle`, late-fusion prediction or fused feature `Z_t`, provenance and alignment confidence.

**Candidate approaches:** modality-specific models + late-fusion logistic/GBDT baseline; masked concatenation; optional cross-attention only after evidence that sample size and alignment justify it.

**Labels:** inherited from the specific downstream prediction task; fusion itself has no universal cognitive target.

**Evaluation:** compare text-only, visual-only, interaction-only, pairwise combinations and all available modalities on the same eligible cohort; report macro-F1/AUROC, Brier/ECE, confidence intervals, and missing-modality robustness. Ablation must not imply causal contribution.

## Module 6: Cognitive State Estimator

**Purpose:** produce bounded, uncertainty-aware estimates for explicitly operationalized state variables.

**Inputs:** evidence bundles, known concept/task metadata and valid prior state/history.

**Outputs:** target-specific probabilities or scores, uncertainty, abstention status, evidence references and target definition.

**Candidate approaches:** prior/majority baseline, logistic regression, gradient boosting, then temporal model; compare modality-specific and fused models. State dimensions without labels remain unknown or human-entered; do not synthesize targets from proxies.

**Labels:** only labels with construct validity for the target. Candidate datasets may provide affect/engagement annotations, correctness, representation content, or performance; these are distinct constructs. A mismatch detector requires its own operational definition and labels.

**Evaluation:** target-specific discrimination/regression metrics, calibration, selective risk/coverage, participant-held-out evaluation and error analysis. Report agreement if human labels are noisy.

## Module 7: Representation Planner

**Purpose:** select an inspectable next action from a constrained action set while preserving teaching continuity.

**Inputs:** concept/goal/current frame, current representation, content affordances, learner request, state estimate and its uncertainty, constraints, prior branch state.

**Outputs:** `RepresentationPlan` with action, target concept, representation form, rationale, evidence IDs, branch parent/return point and an observable follow-up measure.

**Initial method:** deterministic rules and user/teacher choice. If estimates are missing or uncertain, ask a diagnostic question or present options. Never treat a rule as proof that a modality is best for a learner.

**Later method:** supervised/ranking or causal decision model only with data containing available options, exposure, action assignment, context and outcomes. Avoid biased logged choice imitation. No RL in the initial project.

**Labels:** initially none. Future target could be a prespecified outcome-based preference/action value collected under a defensible assignment design.

**Evaluation:** policy feasibility, rationale/provenance completeness, continuity errors, action coverage; later outcome comparison under randomized or valid causal design. Offline logged-policy metrics require known propensities and overlap.

## Module 8: Outcome Recorder and State Updater

**Purpose:** record post-action evidence and create a new state version without overwriting history.

**Inputs:** representation plan, exposure/usage confirmation, follow-up items, response/performance, optional self-report and subsequent events.

**Outputs:** `OutcomeRecord`, new event-sourced state version, return/replan signal.

**Initial method:** transparent state persistence/update rules; retain observed outcomes separately from inferred constructs.

**Labels:** observed follow-up outcomes; cognitive labels only if explicitly collected and validated.

**Evaluation:** outcome completeness, state transition auditability, leakage checks, and later prediction metrics if a next-outcome model is trained.

## Module 9: Experiment and Model Registry

**Purpose:** make training and evaluation reproducible.

**Inputs:** approved dataset version, split manifest, feature schema, model configuration and random seed.

**Outputs:** trained artifacts, training logs, evaluation reports, calibration artifacts and metadata.

**Required metadata:** dataset license/access basis, cohort/split IDs, preprocessing version, target definition, model/library versions, hyperparameter search boundary, random seeds and artifact checksum.

**Evaluation:** auditability and reproducibility checks; this module does not make research claims itself.
