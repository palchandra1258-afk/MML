# MCP-RI Technical Architecture

## Purpose and research boundary

MCP-RI studies whether multimodal evidence can support a temporally grounded, concept-grounded and uncertainty-aware representation of learner context, and whether that representation can improve subsequent knowledge representation choices. The system is a research prototype, not a general cognition reader. Observable behavior is evidence, not a definitive diagnosis: an incorrect answer, pause, retry or request for help must never be mapped directly to “confusion” without validated labels and an appropriate study.

The research reference proposes four layers. The architecture below preserves those layers and makes a distinction between (a) models that can be trained and evaluated with existing targets, (b) hypotheses that require new annotations or a purpose-built study, and (c) non-learning orchestration and safety rules. Dataset availability, rights, schemas, labels and licensing must be verified before a dataset is selected. The list in the research reference is a candidate inventory, not a claim that each dataset is currently accessible or suitable.

**Implementation status:** Phase 9 adds a replayable EdNet behavioral-history state object with per-skill summaries, recent trends, evidence counts and uncertainty intervals. Phase 10 adds normalized evidence records and adapters; Phase 11 adds a separate, traceable rule-based cognitive-state estimate; Phase 12 adds a rule-based representation recommendation and plan history; Phase 13 adds rule-based trajectory/diversion orchestration with context preservation and resumption history. These are bounded foundations, not validated cognitive estimation, prerequisite mastery, or learning-effective representation selection. Learned multimodal encoders/fusion and the post-intervention outcome loop remain research architecture/specification.

Phase 14 adds a local FastAPI integration layer and SQLite/Alembic persistence. Phase 9–12 snapshots remain read-only JSONL and are served through offset indexes; Phase 13 trajectory writes made through HTTP preserve immutable versions and append-only events. Model inference, authentication, and HTTP diversion mutations are not implemented. See [`PHASE14_BACKEND_ARCHITECTURE.md`](PHASE14_BACKEND_ARCHITECTURE.md) and [`BACKEND_INTEGRATION_REPORT.md`](BACKEND_INTEGRATION_REPORT.md).

## System context

```text
Teaching context / concept / current frame / representation
                         │
                         ▼
1. Multimodal Evidence Modeling
   language + optional audio + visual artifacts + event trajectory
                         │  evidence bundle Z_t, modality masks, provenance
                         ▼
2. Cognitive State Estimation
   concept-grounded state estimate + uncertainty + evidence references
                         │  state estimate S_t
                         ▼
3. Representation Intelligence
   inspectable plan / diagnostic question / continuation / diversion
                         │  action R_t and rationale
                         ▼
4. Outcome and State Update
   subsequent evidence + observed outcome + updated state S_(t+1)
                         └───────────────────────────────↺
```

Each event is time-stamped and linked to a learner/session pseudonym, concept and teaching position when those are known. The system records evidence provenance and model/version metadata so that an inference can be inspected and replayed. A missing modality is represented as missing, never as a negative observation. The learner state is an estimate with a confidence/uncertainty field, not an asserted fact.

## Shared data contracts

The implementation should define versioned schemas before model training. Minimum logical objects:

| Object | Required fields | Notes |
|---|---|---|
| `SessionContext` | pseudonymous learner/session IDs, domain/concept IDs if supplied, task/goal, current teaching position, current representation, timestamps | Never infer concept identity solely from a behavioral pattern. |
| `ObservationEvent` | event ID, timestamp or interval, modality, payload reference or derived feature, source, quality, missingness, consent/access metadata | Keep raw data separate from derived features and limit retention. |
| `EvidenceBundle` | aligned event window, per-modality features, modality-availability mask, provenance, alignment quality | Bundling window and synchronization tolerance are dataset-specific and documented. |
| `StateEstimate` | concept/context references, explicitly supported state dimensions, probabilities or intervals, uncertainty/calibration metadata, evidence event IDs, model version | Only include dimensions for which suitable targets or validated inference procedures exist. “Unknown” is a valid value. |
| `RepresentationPlan` | action type, target concept, intended objective, representation form, rationale/evidence, constraints, branch parent/return point, expected observable outcome | Initially rule-based and inspectable; no claim that plan is optimal. |
| `OutcomeRecord` | exposure/action, follow-up task or response, observed correctness/performance, delay, missingness, outcome definition | Separate observed outcomes from latent learning or cognition. |

## Layer 1 — Multimodal Evidence Modeling

### Responsibilities

1. Ingest whichever modalities a selected study actually contains: linguistic text, optional audio, visual artifacts (e.g. diagram or handwriting) and interaction/event sequences.
2. Normalize timestamps, derive task/context windows and retain modality-specific quality and availability metadata.
3. Produce modality-specific features and a fused evidence representation. Compare late fusion and simple concatenation before more complex cross-attention or multimodal transformers.
4. Represent cross-modal agreement/disagreement as candidate features for research; do not encode disagreement as a cognitive label.

### Candidate approaches

- **Text:** pretrained sentence/document encoder or TF-IDF/word n-gram baseline. Use pretrained inference without fine-tuning first. Train a task head only when the target labels exist.
- **Speech:** an existing pretrained ASR model may transcribe audio for analysis. ASR output and confidence are uncertain derived evidence, not ground truth. Do not train ASR for this project initially. Audio-only prosody features are optional and require a dataset with compatible audio and a justified target.
- **Visual artifacts:** pretrained OCR/vision encoder inference where suitable; compare with transparent engineered features and human-coded representation categories. Fine-tune only if task-specific labeled artifacts and sufficient sample size are available.
- **Interaction:** aggregate counts, intervals, order, edits, answer changes and action transitions as observed events. Treat them as behavior features, not direct cognition labels. Begin with hand-engineered features and logistic/GBDT baselines.
- **Fusion:** modality-wise standardized features with explicit masks; late fusion is the first multimodal baseline. Compare against concatenation and, only if data supports it, cross-attention.
- **Temporal:** fixed windows / summary statistics first, then GRU or temporal convolution, and only later a transformer if data volume and split design justify it.

### Outputs

`EvidenceBundle` with modality-specific features, optional fused vector `Z_t`, modality mask, source event IDs, model versions, timestamp/window and quality indicators. The layer does not output “confused,” “understands,” or any other ungrounded cognitive conclusion.

### Phase 10 implementation status

The current implementation is an evidence-record foundation, not the feature-encoder/fusion design above. `src/mcp_ri/evidence/` provides versioned validation, normalization, provenance-preserving adapters, possible-duplicate links, explicit conflict records, conservative alignment/grouping, and an interaction-only bridge to Phase 9. EdNet KT1 is the only real learner modality in this workspace; text/audio/visual adapters are tested synthetically. There is no ASR, OCR, learned fusion, or cognitive interpretation. See [`MULTIMODAL_EVIDENCE_ARCHITECTURE.md`](MULTIMODAL_EVIDENCE_ARCHITECTURE.md) and [`PHASE10_EVALUATION.md`](PHASE10_EVALUATION.md).

Phase 11 consumes the complete Phase 9 snapshot plus matching Phase 10 evidence prefix and emits a separate state record. The estimator checks evidence counts, learner identity, provenance references, timestamps, source sequence and requested cutoff before applying documented rules. It preserves contradictions and only recommends further diagnostic evidence. It does not interpret raw text/audio/visual content or claim a cognitive probability. See [`COGNITIVE_STATE_ARCHITECTURE.md`](COGNITIVE_STATE_ARCHITECTURE.md) and [`COGNITIVE_STATE_METHODOLOGY.md`](COGNITIVE_STATE_METHODOLOGY.md).

## Layer 2 — Cognitive State Estimation

### Implemented component and boundary

`src/mcp_ri/learner_state/` implements response-history summaries, not cognition inference. `src/mcp_ri/cognitive_state/` adds a distinct, provisional projection with explicit uncertainty dimensions, hypotheses, recommendations, and append-only state versions. Both use observed correctness and dataset skill tags; neither measures understanding. Phase 11 keeps estimate confidence low because EdNet has no corresponding ground-truth labels. See [`LEARNER_STATE_ARCHITECTURE.md`](LEARNER_STATE_ARCHITECTURE.md), [`COGNITIVE_STATE_ARCHITECTURE.md`](COGNITIVE_STATE_ARCHITECTURE.md), and [`COGNITIVE_STATE_METHODOLOGY.md`](COGNITIVE_STATE_METHODOLOGY.md).

### State representation

State dimensions should be introduced only where the study has defensible operational labels. Candidate dimensions from the research reference include concept, objective, estimated understanding, uncertainty, potential misconception, representation difficulty/need, current teaching position and diversion context. These are not all necessarily observable or labeled in the candidate public datasets.

Use a structured estimate with three categories:

- **Observed:** recorded response, event, artifact, self-report or annotation.
- **Inferred:** model output tied to a defined target and evidence window.
- **Unknown:** not measured or not supported by evidence.

Never collapse those categories. An outcome label such as next-question correctness can supervise prediction of next-question correctness; it cannot silently be renamed cognitive state.

### Candidate models

- Static supervised baselines: majority/stratified prior, logistic regression, linear SVM and gradient-boosted trees on valid task labels.
- Temporal state estimators: persistence/last-observation baseline, then a GRU or temporal convolution over event windows if participant/session counts and label coverage permit.
- Multimodal state models: late fusion over modality-specific outputs; compare with each unimodal system and with interaction-only/mastery-only baselines.
- Representation mismatch detection: initially a prespecified rule/annotation target or a human-coded study label. Train only after mismatch is operationalized and labeled independently of model features.

### Outputs

`StateEstimate`: target-specific class probabilities or regression estimate; uncertainty; calibration metadata; evidence references; target definition; and abstention/unknown status. A model must not emit an interpretable cognitive claim outside its trained target.

## Layer 3 — Representation Intelligence

### Initial operation

Use an inspectable, deterministic policy over explicit inputs: current concept and goal; current representation; available content/representation options; state estimates and uncertainty; learner request; teaching position; and system constraints. Policy outputs include continue, answer/clarify, ask a diagnostic question, offer an example, change representation, create a temporary diversion, or return/replan. If evidence is weak or modalities conflict, prefer a low-cost diagnostic question or user choice instead of asserting a state. The policy records its rule, evidence and branch return point.

This layer is not initially trained as a representation selector. Existing datasets generally do not provide randomized representation assignments and outcomes for all options, so a model trained to imitate observed choices would reproduce historical selection bias and would not establish which representation improves learning.

### Phase 12 implementation status

`src/mcp_ri/representation/` implements a deterministic rule engine over Phase 11 states and their embedded Phase 9 observations. It records satisfied/unsatisfied conditions, evidence IDs, alternatives, registry availability, objective/content gaps and preserved context. The registry is unavailable for all actual delivery categories in this repository; plans request more evidence or defer unless a provider/content source is explicitly supplied. EdNet tags map to item identifiers only. The module does not generate content, run interventions or claim educational effectiveness. See [`REPRESENTATION_INTELLIGENCE_ARCHITECTURE.md`](REPRESENTATION_INTELLIGENCE_ARCHITECTURE.md) and [`REPRESENTATION_EVALUATION.md`](REPRESENTATION_EVALUATION.md).

### Phase 13 implementation status

`src/mcp_ri/trajectory/` adds versioned primary trajectories, an explicit finite-state machine, a conservative diversion detector, a sourced dependency registry, compact parent-context snapshots, bounded diversion progress/revisions, a resumption engine, and append-only reconstructable history. The default prerequisite registry is empty. Synthetic dependencies are opt-in for tests, and capability deferral cannot be interpreted as a knowledge gap. The API history store is in-memory; the bounded runner exports JSONL. No concept prerequisites, actual instructional exposure, or learning effects are inferred from EdNet. See [`LEARNING_TRAJECTORY_ARCHITECTURE.md`](LEARNING_TRAJECTORY_ARCHITECTURE.md) and [`TRAJECTORY_EVALUATION.md`](TRAJECTORY_EVALUATION.md).

### Later trainable decision model

Only after a sufficiently designed study collects state/context, available actions, chosen action, exposure, pre/post outcomes and preferably randomized or otherwise defensibly identified action assignment, train a contextual supervised or causal decision model. Start with offline evaluation and conservative supervised/ranking methods. Consider contextual bandits only with adequate logged action coverage and propensity information or a prospective safe study. Reinforcement learning is out of scope until sequential decision data, meaningful reward definition, sample size and ethical deployment justification exist.

## Layer 4 — Outcome and State Update

Capture the actual selected representation, whether it was shown/used, follow-up response and task, response time if appropriate, self-report if collected, and missingness. Define primary outcomes before analysis (e.g. accuracy on a prespecified concept-aligned follow-up item or gain from a pre-test to post-test). Do not equate engagement, correctness, or dwell time with learning without a construct argument.

Initially update state through transparent event-sourced rules: preserve prior estimates, append observations, decay or expire only by a predeclared policy, and recompute a model estimate only when its input/target contract is met. Keep raw event history immutable for audit; derive new state versions rather than overwriting old estimates. Later train update models only with longitudinal labels and leakage-safe splits.

## Model-development and execution locations

Training occurs in a reproducible research environment, separate from the inference/runtime path. Existing EdNet training scripts consume the processed unseen-learner partitions and save models/reports under experiment-specific paths. The Phase 9 state builder is descriptive and does not load or modify those artifacts. GPU use is optional: classical baselines run on CPU, while the saved temporal models used PyTorch/CUDA. Any future fine-tuning must be an explicit experiment confined to training data. Runtime inference should load a frozen, versioned artifact and should not update weights online in the initial prototype. Exact cloud/provider choice remains undecided pending privacy, dataset terms and compute.

## Cross-cutting evaluation and controls

- Split by learner (and by session/temporal order when appropriate) to prevent leakage; do not randomly split windows from the same learner across train and test.
- Report per-class and per-modality coverage, missingness, confidence intervals and subgroup performance where sample size permits.
- Compare models on identical eligible examples. For modality ablations, use a consistent evaluation cohort or explicitly describe the changed cohort.
- Evaluate calibration and selective prediction in addition to discrimination; permit abstention.
- Record data provenance, preprocessing, random seeds, feature definitions, model versions and label definitions.
- Obtain appropriate ethics review, consent and data-use approvals before collecting or processing identifiable voice/video/physiology.

## Research limitations

Public datasets are fragmented and may not include the modalities, concept-level labels, uncertainty labels, longitudinal outcomes or action assignments required by the end-to-end question. Existing labels often concern engagement, affect, correctness or performance rather than misconception or representational mismatch. Cross-dataset results cannot be treated as a single integrated learner model without careful domain/task validation. A small purpose-built study may be necessary, but its size, protocol and ethics approvals must be determined before collection. The prototype should make bounded, evidence-linked claims rather than claim to infer a person's cognition generally.
