# MCP-RI Implementation Roadmap

This roadmap plans later implementation work. It does not authorize or perform code, data downloads or human-subject collection in this planning stage.

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

## Recommended first model to train

Train a **simple interaction-history model to predict a recorded next-response outcome**—initially logistic regression, with a majority/persistence baseline and optionally gradient-boosted trees for comparison. Use the CMU DataShop equation-solving dataset if its current access, terms, transaction schema, learner IDs and subsequent correctness fields are verified. The research reference identifies this as a constrained interaction/handwriting setting, but it does not establish exact column availability. If those fields are absent, inspect the Math Data Corpus and use only a documented correctness/problem outcome if the data and access support it; otherwise choose another verified dataset or stop before training.

The data required are learner/session identifiers for grouped splits; task/item or concept identifiers if available; ordered interaction/attempt history; timestamps or sequence order; and an explicitly recorded next response correctness/outcome. The target is **next observed response outcome**, not confusion, understanding, uncertainty or representation mismatch.

This should be first because it establishes the data pipeline, target/split discipline, and a transparent lower-complexity baseline before adding modalities or temporal deep learning. It tests one part of the research foundation without pretending that behavioral traces directly reveal cognition. Afterward, the project can test whether verified language/visual modalities add value and whether valid state labels and intervention data can support the broader MCP-RI question.
