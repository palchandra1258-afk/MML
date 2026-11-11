# MCP-RI Research Status and Dataset Inventory

**Status date:** 11 November 2026. This file summarizes the research reference, verified local assets, and implementation status through Phase 13.

## Research problem and intended contribution

MCP-RI asks how a persistent cognitive system can turn heterogeneous evidence from language/voice, visual artifacts, and interaction histories into a temporally persistent, concept-grounded and uncertainty-aware representation, then use that representation to choose how knowledge should be continued, explained, externalized, or temporarily diverted. The motivating case is a learner interrupting a teaching trajectory: the system must preserve the current concept and frame, distinguish a request from a possible representational mismatch, choose a bounded next action, record the outcome, and resume or replan with continuity.

The central research contribution is the bridge across perception, state, representation choice and outcome—not any isolated classifier. The research reference explicitly concludes that no identified public dataset supports the complete end-to-end loop. It recommends component studies on public data followed by a carefully designed, ethically approved longitudinal study if the full loop is to be tested.

## Four-layer architecture

| Layer | Research function | Current evidence boundary |
|---|---|---|
| 1. Multimodal Evidence Modeling | Ingest available language/audio, visual artifacts, interactions and history; align them with modality masks, quality and provenance. Start with modality-specific encoders and late fusion. | EdNet KT1 supplies question-response history and item metadata only. No learner audio, webcam video, diagrams or physiological sensors are in the acquired snapshot. |
| 2. Cognitive State Estimation | Estimate only explicitly defined targets, retaining probabilities, calibration, evidence references and unknown values. | EdNet correctness is an observed outcome and may supervise response prediction/knowledge tracing; it is not a ground-truth cognition label. Cognitive state and representational mismatch remain unlabelled locally. |
| 3. Representation Intelligence | Initially produce inspectable continuation, clarification, diagnostic-question, representation-change or diversion plans with rationale and return pointers. | No acquired dataset records a complete action set, representation exposure, assignment and follow-up outcome. Keep this layer rule-based until such data exists. |
| 4. Outcome and State Update | Record exposure and follow-up outcome; append evidence and create a new state version without overwriting history. | EdNet records later response outcomes but no MCP-RI representation intervention. A future learning-benefit claim requires a controlled, concept-aligned study. |

The system must preserve observed, inferred and unknown information separately. An error, pause, retry or answer change is not a definitive confusion label. Model confidence/calibration is not the learner's subjective uncertainty.

### Phase 9 learner-state module (6 November 2026)

A transparent, replayable behavioral state module now exists at `src/mcp_ri/learner_state/`. It represents observed response history overall and per EdNet skill tag, recent change, Beta-smoothed response performance, Wilson intervals, evidence tiers, and non-diagnostic potential-issue flags. The full validation pass produced states for 117,785 learners (including one validation-assigned learner with no labeled responses) and 3,897,566 learner-skill entries; all states passed schema and numeric consistency checks. The module is a Layer 2 foundation only: its performance estimates are derived from correctness, not cognitive-state labels, and it is not a validated understanding estimator. Full results and limitations are in [`LEARNER_STATE_EVALUATION.md`](LEARNER_STATE_EVALUATION.md).

### Phase 10 evidence modeling (6 November 2026)

The evidence layer now defines versioned evidence, alignment, group and conflict schemas; adapters for interaction, text, audio, visual and Phase 9 temporal-history references; source-preserving normalization; duplicate-candidate retention; conservative grouping/alignment; and an interaction-only Phase 9 bridge. A bounded unseen-learner validation sample is used for real EdNet checks. Text/audio/visual adapters and conflict/alignment edge cases use generated fixtures because EdNet contains no learner-authored text, speech or visual artifacts. This is normalization and evidence organization, not learned multimodal fusion or cognitive inference. See [`MULTIMODAL_EVIDENCE_ARCHITECTURE.md`](MULTIMODAL_EVIDENCE_ARCHITECTURE.md), [`MODALITY_AVAILABILITY_REPORT.md`](MODALITY_AVAILABILITY_REPORT.md), and [`PHASE10_EVALUATION.md`](PHASE10_EVALUATION.md).

### Phase 11 cognitive-state estimation (6 November 2026)

A separate versioned cognitive-state schema and interpretable estimator now consume complete Phase 9 snapshots with matching Phase 10 evidence prefixes. Transparent rules classify concept-level observed performance into provisional statuses, produce evidence-linked hypotheses without misconception labels, retain contradictory evidence, describe separate uncertainty dimensions, and recommend diagnostic information. Append-only snapshots preserve temporal updates. The bounded validation-learner sample emitted 184 snapshots for 100 learners; all passed the Phase 11 validator. Estimate confidence remains low and overall uncertainty high because there are no cognitive-state labels. This validates wiring, traceability, and deterministic rule behavior only, not cognitive accuracy or educational benefit. See [`COGNITIVE_STATE_EVALUATION.md`](COGNITIVE_STATE_EVALUATION.md), [`COGNITIVE_STATE_METHODOLOGY.md`](COGNITIVE_STATE_METHODOLOGY.md), and [`COGNITIVE_STATE_ARCHITECTURE.md`](COGNITIVE_STATE_ARCHITECTURE.md).

### Phase 12 representation intelligence (6 November 2026)

The repository now includes a versioned eight-category representation taxonomy, plan schema, explicit capability registry, rule traces and alternatives, EdNet metadata-only concept grounding, and append-only plan history. The engine consumes Phase 11 states and their Phase 9 behavioral statistics; direct Phase 9 snapshots can be cross-checked. The bounded run uses only Phase 11's validation sample and never evaluates locked-test records. Because no delivery provider or curated instructional content exists locally, real-data plans select no representation for execution. Synthetic tests cover all requested response patterns, conflicts, explicit mismatch annotations, availability fallback, evidence traceability and context/version preservation. This is policy/software verification, not representation effectiveness. See [`REPRESENTATION_EVALUATION.md`](REPRESENTATION_EVALUATION.md), [`REPRESENTATION_AVAILABILITY.md`](REPRESENTATION_AVAILABILITY.md), and [`REPRESENTATION_DECISION_METHODOLOGY.md`](REPRESENTATION_DECISION_METHODOLOGY.md).

### Phase 13 trajectory and resumption orchestration (11 November 2026)

The trajectory layer adds explicit state transitions, evidence-linked diversion reviews, context snapshots, bounded resumption/replanning decisions, and append-only event reconstruction. The bounded validation sample created 100 trajectories and no diversions because the default dependency registry contains no verified prerequisite edges. All observed transitions and evidence references passed the recorded checks; synthetic cases exercise illegal transitions and lifecycle alternatives. This verifies software orchestration and traceability, not learner mastery, cognitive accuracy, representation effectiveness, or learning gain. History is in memory and exported as local JSONL; durable database storage and a validated curriculum graph remain unimplemented. See [`PHASE13_IMPLEMENTATION_REPORT.md`](PHASE13_IMPLEMENTATION_REPORT.md), [`TRAJECTORY_STATE_MACHINE.md`](TRAJECTORY_STATE_MACHINE.md), and [`TRAJECTORY_EVALUATION.md`](TRAJECTORY_EVALUATION.md).

## Dataset inventory in this workspace

### Acquired and locally usable

**EdNet KT1 + question-content table** is the only learner dataset acquired in this workspace. Raw archives are preserved under `data/raw/ednet/`; processed features and quality summaries are under `data/processed/ednet/`. The validated snapshot has 784,309 learner files, 95,293,926 KT1 interaction rows, 13,169 question records, and 95,266,280 answer-key-derived correctness targets. The EdNet license is CC BY-NC 4.0: preserve attribution and restrict use to non-commercial purposes. Do not redistribute the raw snapshot.

KT1 supports ordered question-response behavior. It does not contain synchronized learner speech/video or validated confusion, understanding, misconception, uncertainty, representation-choice or intervention-benefit labels. EdNet is TOEIC/English tutoring data, whereas the research's motivating examples emphasize mathematical representations; domain transfer is unresolved.

### Candidate datasets not acquired here

| Candidate | Useful component if access/terms pass review | Status and construct limit |
|---|---|---|
| CMU DataShop equation-solving project | Constrained interaction/outcome replication; possibly handwriting if current linked files are actually available | Project-specific access, exports, media, fields and reuse terms remain unverified. General DataShop schema is not proof of this project's columns. |
| Math Data Corpus / MMLA Grand Challenge | Speech + digital pen/image alignment and documented group problem/content labels | Current access and rights-holder agreement need confirmation; group labels are not automatically individual cognitive labels. |
| MUTLA | Logs/video/EEG and its documented annotations for a separate component study | Current files, license/terms and exact labels need verification; engagement is not conceptual mismatch. |
| EduMUSE | Text/figure/exercise content and representation inventory | Content resource, not learner behavior or state training data. |
| OULAD | Course-level clickstream/assessment prediction | No item-level next-answer stream or rich learner multimedia. |
| ES-KT-24 | Candidate multimodal knowledge-tracing benchmark | Must verify current files, schema, label granularity and terms before use; KT targets do not establish cognition. |
| PE-HRI, BBBD, DAiSEE, NUSMSP, SOPHIAS | Narrow collaboration, sensor, affect or presentation components | Different populations/constructs; not substitutes for concept-grounded representation intervention data. |

The dataset analysis and access guide document their sources and unresolved access gates. A research reference or link is not evidence that a dataset is downloaded, licensed for this use, or suitable for a model target.

## Completed EdNet experiments

The existing EdNet work defines the target as whether the next submitted answer is correct and excludes the current answer, answer key, correctness and post-response elapsed time from inputs. Learners are split before model training; the unseen-learner test partition has not been evaluated.

| Model | Training setup | Validation result summary |
|---|---|---|
| SGD logistic regression | 5% deterministic training-learner sample; 3,255,537 examples from 27,310 learners | Accuracy 0.7075, F1 0.8021, ROC-AUC 0.7413, AP 0.8350, log loss 0.5648, Brier 0.1916, ECE 0.0358 on 14,236,525 validation examples. |
| Random Forest | Same feature/learner sample; sparse matrix; shallow trees | Near-prevalence accuracy and worse discrimination/loss than logistic. |
| XGBoost 300 and resumed 600 rounds | Same sample/features; CPU histogram trees; early-stop validation subset; 600-round cap reached | Continued XGBoost improves on its first run but remains behind logistic on most predictive metrics; lower ECE is not proof of general calibration. |

These are validation results and model-selection evidence, not final test results or claims about cognitive state. The detailed experiment reports preserve all exact metrics and resources.

## Completed temporal-model study

DKT-style LSTM and SAKT-style causal attention networks were trained from scratch in run `phase8-temporal-20261105T073420Z-seed2025`. They used the same deterministic 5% learner sample as the Phase 6–7 EdNet work: 3,255,537 response labels and 3,228,227 temporal transitions across 27,310 training learners. A separate learner-hash split assigned validation learners to early stopping, temperature scaling, and report-only evaluation. The final matched report cohort contains 11,382,220 transitions from 90,982 unseen learners; each learner's first response was excluded from all models because it has no prior history. No test labels were used or evaluated.

On this cohort, SAKT achieved accuracy 0.7133, ROC-AUC 0.7464, average precision 0.8411, log loss 0.5551, and Brier score 0.1880, versus matched logistic scores of 0.7085, 0.7424, 0.8366, 0.5634, and 0.1911. Logistic retained higher F1. Learner-macro uncertainty shows that the pooled accuracy improvement is not clearly a typical-learner accuracy gain. Also, logistic uses engineered item/skill/history features while the sequence models use question IDs and prior correctness; the comparison does not isolate architecture alone. Results and limits are detailed in [`TEMPORAL_KNOWLEDGE_TRACING_EXPERIMENT.md`](TEMPORAL_KNOWLEDGE_TRACING_EXPERIMENT.md) and [`PHASE8_SEQUENCE_MODEL_COMPARISON.md`](PHASE8_SEQUENCE_MODEL_COMPARISON.md).

The models predict a recorded answer outcome only. They do not validate multimodal state estimation, cognition, representation selection, or learning benefit. The published EdNet SAINT+ score is a useful reference but uses a different snapshot, much larger training set and held-out test protocol; direct performance equivalence has not been established.

## Main gaps and next research gates

1. Acquire or receive approval for a dataset with synchronized language, visual artifact and interaction modalities plus a common, clearly defined target—or design a new study.
2. Operationalize cognition/mismatch constructs independently; collect self-report or expert annotations with a documented procedure and inter-rater analysis. Do not derive these labels from correctness/retries alone.
3. Add reviewed, concept-grounded representation assets and real delivery providers to the Phase 12 planner; verify actual concept alignment and availability before content can be selected.
4. For intervention-benefit claims, collect exposure, action availability/assignment, pre/post concept-aligned outcomes and adequate action coverage, preferably under randomization/counterbalancing.
5. Before scaling EdNet beyond 5%, predeclare the evaluation estimand and compute budget. Retrain all compared baselines on the same expanded learner set; freeze model, calibration, and analysis choices before a single locked-test evaluation. A separate time-forward known-learner study addresses a different deployment question.
6. Treat public-paper numbers as comparable only when dataset, population, target, preprocessing, split, metric and evaluation protocol match. No outcome can be guaranteed to equal or exceed a paper's score in advance.
