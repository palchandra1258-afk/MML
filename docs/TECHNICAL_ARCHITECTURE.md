# MCP-RI Technical Architecture

## Purpose and research boundary

MCP-RI studies whether multimodal evidence can support a temporally grounded, concept-grounded and uncertainty-aware representation of learner context, and whether that representation can improve subsequent knowledge representation choices. The system is a research prototype, not a general cognition reader. Observable behavior is evidence, not a definitive diagnosis: an incorrect answer, pause, retry or request for help must never be mapped directly to “confusion” without validated labels and an appropriate study.

The research reference proposes four layers. The architecture below preserves those layers and makes a distinction between (a) models that can be trained and evaluated with existing targets, (b) hypotheses that require new annotations or a purpose-built study, and (c) non-learning orchestration and safety rules. Dataset availability, rights, schemas, labels and licensing must be verified before a dataset is selected. The list in the research reference is a candidate inventory, not a claim that each dataset is currently accessible or suitable.

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

## Layer 2 — Cognitive State Estimation

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

### Later trainable decision model

Only after a sufficiently designed study collects state/context, available actions, chosen action, exposure, pre/post outcomes and preferably randomized or otherwise defensibly identified action assignment, train a contextual supervised or causal decision model. Start with offline evaluation and conservative supervised/ranking methods. Consider contextual bandits only with adequate logged action coverage and propensity information or a prospective safe study. Reinforcement learning is out of scope until sequential decision data, meaningful reward definition, sample size and ethical deployment justification exist.

## Layer 4 — Outcome and State Update

Capture the actual selected representation, whether it was shown/used, follow-up response and task, response time if appropriate, self-report if collected, and missingness. Define primary outcomes before analysis (e.g. accuracy on a prespecified concept-aligned follow-up item or gain from a pre-test to post-test). Do not equate engagement, correctness, or dwell time with learning without a construct argument.

Initially update state through transparent event-sourced rules: preserve prior estimates, append observations, decay or expire only by a predeclared policy, and recompute a model estimate only when its input/target contract is met. Keep raw event history immutable for audit; derive new state versions rather than overwriting old estimates. Later train update models only with longitudinal labels and leakage-safe splits.

## Model-development and execution locations

Training occurs in a reproducible research environment, separate from the inference/runtime path. Training scripts/notebooks (to be created in a later implementation phase) consume versioned, permission-checked dataset partitions and write model artifacts, metrics and metadata to a controlled experiment directory. GPU use is optional: classical baselines should run on CPU; pretrained encoders may run locally or on a managed GPU depending on size. Fine-tuning is a later, explicit experiment and must use the training split only. Runtime inference loads a frozen, versioned artifact; it never updates weights online in the initial prototype. Exact cloud/provider choice is intentionally undecided pending privacy, dataset terms and available compute.

## Cross-cutting evaluation and controls

- Split by learner (and by session/temporal order when appropriate) to prevent leakage; do not randomly split windows from the same learner across train and test.
- Report per-class and per-modality coverage, missingness, confidence intervals and subgroup performance where sample size permits.
- Compare models on identical eligible examples. For modality ablations, use a consistent evaluation cohort or explicitly describe the changed cohort.
- Evaluate calibration and selective prediction in addition to discrimination; permit abstention.
- Record data provenance, preprocessing, random seeds, feature definitions, model versions and label definitions.
- Obtain appropriate ethics review, consent and data-use approvals before collecting or processing identifiable voice/video/physiology.

## Research limitations

Public datasets are fragmented and may not include the modalities, concept-level labels, uncertainty labels, longitudinal outcomes or action assignments required by the end-to-end question. Existing labels often concern engagement, affect, correctness or performance rather than misconception or representational mismatch. Cross-dataset results cannot be treated as a single integrated learner model without careful domain/task validation. A small purpose-built study may be necessary, but its size, protocol and ethics approvals must be determined before collection. The prototype should make bounded, evidence-linked claims rather than claim to infer a person's cognition generally.
