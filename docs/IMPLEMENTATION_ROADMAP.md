# MCP-RI Implementation Roadmap

This roadmap records both planned research work and implemented foundations. Phase 13 is now a bounded orchestration prototype; further data downloads and human-subject collection remain separately gated by terms, protocol, consent, and ethics review.

## Phase 0 — Research specification and decisions

**Tasks**

- Confirm the canonical project name and maintain the existing research direction.
- Select one constrained initial concept/task and one primary outcome.
- Translate the research reference's candidate datasets into a verified data-access/label matrix.
- Define the first model's target as an observable outcome, unless valid state labels are confirmed.
- Decide initial compute and data-handling environment based on dataset terms/privacy.

**Exit criteria**

- A target and construct definition exist.
- Dataset schema, access, terms, modalities and label fields are checked.
- Feasibility and split unit are documented; no missing target is synthesized.

## Phase 1 — Data contract and reproducibility foundation

**Tasks**

- Define versioned event/context/evidence/target/outcome schemas.
- Specify pseudonymous learner/session keys, modality masks, provenance and timestamp conventions.
- Create experiment tracking conventions and a frozen split manifest.
- Document privacy, retention and any required ethics approval.

**Exit criteria**

- A sample can be validated and traced from source row to analysis example.
- No model feature is derived from post-target information.

## Phase 2 — First trainable baseline

**Tasks**

- Build target prevalence and persistence baselines.
- Train a logistic regression interaction-history model; compare a gradient-boosted tree if sample/field structure supports it.
- Evaluate learner-held-out and, where possible, time-forward performance.
- Add probability metrics and calibration assessment.

**Exit criteria**

- Training uses only train partition; final evaluation uses held-out learners.
- Results are reproducible and target is named accurately.
- The model is explicitly described as outcome prediction, not cognition detection.

## Phase 3 — Evidence encoders and modality ablations

**Tasks**

- Add only modality encoders for data actually present: frozen text, optional ASR, visual/pen, interaction.
- Evaluate each modality independently on a common target and cohort.
- Add late fusion and missing-modality masks.
- Compare modality performance with uncertainty and confidence intervals.

**Exit criteria**

- Synchronized features and label availability are verified.
- Improvement claims use matched cases and appropriate statistical uncertainty.

## Phase 4 — Temporal and calibrated state estimation

**Tasks**

- Compare static features and persistence against GRU/temporal convolution.
- Introduce state estimation only if repeated validated state labels exist.
- Add calibration/abstention and evidence-linked state records.
- For mismatch research, define and annotate the construct independently.

**Exit criteria**

- Temporal splits avoid leakage.
- Model targets match construct labels and uncertainty is evaluated.
- State dimensions without adequate evidence remain unknown.

## Phase 5 — Initial Representation Intelligence prototype

**Tasks**

- Implement constrained representation/action inventory and inspectable rules.
- Add low-confidence diagnostic question or learner choice fallback.
- Record action rationale, evidence, branch parent and return point.
- Test continuity and plan feasibility independently from claims of learning benefit.

**Exit criteria**

- Every plan is auditable and refers to available content/actions.
- Interruption and return behavior preserves the original teaching context.

## Phase 13 implementation checkpoint — Trajectory and diversion orchestration

**Implemented foundation**

- Added versioned primary trajectory, diversion, context snapshot, dependency registry, and event schemas.
- Added explicit state transitions, conservative evidence-linked diversion rules, bounded diversion progress and revision, resumption/replanning, and reconstructable append-only history.
- Integrated stable references to Phases 9–12 while leaving their schemas unchanged.
- Added a bounded validation-snapshot runner, technical evaluator, history validator, synthetic tests, and Phase 13 documentation.

**Research gates still open**

- No dataset-sourced prerequisite graph or validated curriculum objective is available; the production default registry remains empty.
- No representation delivery provider or post-intervention outcomes exist.
- History is in-memory in the API and exported as JSONL by the runner; production durable/concurrent persistence remains future implementation work.
- Technical validation does not establish cognitive accuracy, mastery, or learning improvement.

See [`LEARNING_TRAJECTORY_ARCHITECTURE.md`](LEARNING_TRAJECTORY_ARCHITECTURE.md), [`TRAJECTORY_EVALUATION.md`](TRAJECTORY_EVALUATION.md), and [`PHASE13_IMPLEMENTATION_REPORT.md`](PHASE13_IMPLEMENTATION_REPORT.md).

## Phase 6 — Outcome loop and prospective evaluation

**Tasks**

- Define a concept-aligned pre/post outcome and study protocol.
- Plan sample size/power, randomization/counterbalancing and analysis before collection.
- Obtain ethics/consent approval as required.
- Collect action assignment, exposure, usage and outcomes; evaluate fixed, rule-based and state-aware conditions.

**Exit criteria**

- The study can distinguish prediction from intervention effect.
- Action comparisons have adequate coverage and valid identification.
- State updates use observed outcomes without rewriting history.

## Phase 7 — Optional learned decision policy

**Prerequisites**

- Adequate longitudinal action-outcome data, known action availability and exposure, credible assignment/propensity information, a meaningful prespecified reward/outcome, and ethical deployment controls.

**Tasks**

- Begin with supervised ranking/value estimation and rigorous offline evaluation.
- Consider a contextual bandit only with sufficient coverage and safe prospective validation.
- Consider sequential RL only if sequential effects and delayed outcomes demand it and the dataset/design supports identification.

**Exit criteria**

- Learned policy demonstrates robust improvement over simple policies under valid evaluation and has an uncertainty/override strategy.

## Dependencies and decision gates

| Dependency | Why it matters | Gate |
|---|---|---|
| Dataset access and terms | Determines permissible use, storage and publication | Before downloading or preprocessing |
| Actual modality/label schema | Determines which model can be trained | Before defining model target |
| Learner IDs and timestamps | Needed for leakage-safe and temporal splits | Before evaluation design |
| Construct/annotation protocol | Needed for cognitive/mismatch claims | Before state-model training |
| Compute | Determines frozen inference vs fine-tuning feasibility | Before model selection |
| Ethics/consent | Required for new participant data and sensitive modalities | Before collection |
| Action-outcome design | Needed to learn representation selection credibly | Before any policy-training claim |

## Main technical risks and responses

- **No end-to-end public dataset:** stage component studies; plan a controlled dataset only after feasibility and ethics review.
- **Proxy labels mistaken for cognition:** name targets precisely and retain observed/inferred/unknown distinction.
- **Over-complex modeling:** require baseline wins, matched comparisons and sufficient independent learners before deep architectures.
- **Sparse/misaligned modalities:** use modality masks, late fusion, modality-specific evaluation and no forced imputation.
- **Confounded representation choices:** use rule-based prototype first; design prospective randomized/counterbalanced outcome study before learning a policy.
- **Overclaiming calibration:** calibrate on held-out data and re-evaluate under shift; uncertainty is distribution dependent.

## Completed first behavioral prediction model and next step

The initial observable-outcome model was completed on EdNet KT1, selected after dataset access and label verification. SGD logistic regression predicts whether a learner's next submitted answer is correct; it is a behavioral response prediction, not a direct measure of understanding, confusion, uncertainty, or cognitive state. The Phase 6 run and the Phase 7 tree comparisons are documented in their experiment reports.

Phase 8 added DKT and SAKT-style sequence models on the same 5% sampled training-learner protocol. SAKT improved several pooled response-prediction metrics on a matched unseen-learner validation cohort, while logistic retained higher F1. The validation test partition remains untouched. The comparison is not architecture-only because the sequence and tabular models consume different feature representations. See [`TEMPORAL_KNOWLEDGE_TRACING_EXPERIMENT.md`](TEMPORAL_KNOWLEDGE_TRACING_EXPERIMENT.md), [`PHASE8_SEQUENCE_MODEL_COMPARISON.md`](PHASE8_SEQUENCE_MODEL_COMPARISON.md), and [`PHASE8_CALIBRATION_ANALYSIS.md`](PHASE8_CALIBRATION_ANALYSIS.md).

Before a larger run, predeclare whether the primary estimand weights each response or each learner, select the primary metric, budget tuning, then retrain all relevant baselines on the same expanded learner set. Freeze the analysis before any single test evaluation. This line of work strengthens only the EdNet behavioral-prediction component. The multimodal cognitive-state and representation-selection hypotheses still require data with verified modality alignment and independently defined construct labels, followed by prospective intervention/outcome evaluation.
