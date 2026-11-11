# Complete Repository Audit — MCP-RI

**Audit date:** 6 November 2026

**Scope:** Repository files and locally available data/model/result artifacts. This is an implementation and evidence audit, not a new experiment.

## 1. Executive summary

The repository contains a substantial research specification, a verified EdNet KT1 acquisition/validation/preprocessing pipeline, and completed behavioral next-response prediction experiments. It includes a sampled SGD logistic model, Random Forest, two XGBoost checkpoints (300 and 600 rounds), and Phase 8 DKT and SAKT-style sequence models. The saved experiment records report validation-only performance; no locked test partition has been scored.

The originally reported Phase 6 result is corroborated by the JSON report and metric CSV: 3,255,537 training responses from 27,310 learners, 14,236,525 validation responses, and logistic accuracy 0.707515, F1 0.802130, ROC-AUC 0.741321, AP 0.835027, log loss 0.564780, Brier 0.191647, ECE 0.035780. All stated Phase 6 baseline values also match the stored artifacts.

The data pipeline is more mature than the core MCP-RI system. EdNet yields ordered behavioral interactions and item metadata, not audio, video, diagrams, learner-state labels, intervention records, or evidence of learning benefit. The next-answer models do **not** constitute cognitive-state estimators. Layers 1–4 of the proposed system are not integrated; most of their core functions remain planned or absent.

Important qualification: Phase 8's completed report contains credible evidence of DKT and SAKT-style training and matched report-only validation, but its saved weights could not be loaded in this audit environment because PyTorch is unavailable. Likewise, `joblib` is missing here, preventing independent loading checks for the scikit-learn models. The XGBoost JSON artifacts are present, but the XGBoost runtime is not installed in this interpreter. Artifact presence and report status are therefore verified; runtime deserialization/inference is not.

The repository's Python test discovery run produced **15 passes, 1 skipped module, and 2 import errors**. Preprocessing, validation and shard-merge tests passed. The skipped ML pipeline module and the import errors reflect absent dependencies in the current interpreter (`joblib`, `torch`), not demonstrated test assertion failures. Existing documentation records a focused Phase 8 smoke suite passing in the original training environment; that environment was not available for this audit run.

## 2. Repository structure and how the pieces connect

- `MML-Research-Project (1).md` is the original research framing. It motivates persistent multimodal evidence, cognitive context, representation choices and interruption/return continuity. It also contains a broad, historical candidate-dataset and literature survey; those mentions do not mean those datasets were acquired.
- `docs/` contains architecture, data access/selection, schema and preprocessing policy, feature and split decisions, experiment designs, phase reports and research-status summaries. Architecture/module/data-flow documents primarily specify planned behavior; they are not executable implementations.
- `src/mcp_ri/ednet_validation.py` validates EdNet schemas, archive contents, question-content mapping, timestamp ordering, answer-key availability and aggregate data quality. `ednet_preprocessing.py` constructs per-event labels, split assignments and strictly prior history features. `models/ednet_logistic.py` provides the sparse encoder, feature whitelist, sampling and metrics used by training code.
- `scripts/acquire_ednet.py`, `validate_ednet.py`, `preprocess_ednet.py` and `merge_ednet_shards.py` form the acquisition-to-processed-table pipeline. `scripts/training/` holds separate baseline, advanced tabular, XGBoost continuation and temporal sequence training entry points.
- `data/raw/ednet/` holds two local ZIP archives and acquisition metadata. `data/processed/ednet/` holds one 5.89 GB compressed row-level table plus aggregate quality/provenance summaries. The raw and processed large files are ignored by Git; the metadata and JSON summaries are present in the workspace.
- `models/` contains the baseline definition, saved fitted encoder, logistic classifier, Random Forest, XGBoost JSON boosters and PyTorch checkpoints. There are no deployment-serving/application components.
- `results/reports/`, `results/tables/`, and `results/figures/` preserve run states, experiment configurations, validation metrics, calibration bins, bootstrap summaries, importance summaries and reliability diagrams. One Phase 7 run is explicitly interrupted before matrix creation; one Phase 8 run failed on an attention-mask shape error; later runs completed.
- `tests/` contains six test modules covering validation, preprocessing, shard merging, the baseline pipeline, advanced models and sequence models. No notebooks, separate training log files, application/UI files, or end-to-end MCP-RI integration are present in the repository file inventory.
- `requirements-training.txt` pins scikit-learn and XGBoost. `requirements-deep-learning.txt` pins a CUDA 13 PyTorch build; the current audit interpreter does not have these dependencies installed.

`README.md` accurately describes EdNet behavior prediction as distinct from cognition, but is behind the repository: it omits Phase 8, lists only three training entry points, and describes reports mainly as Phase 6/7. `docs/EDNET_DATA_QUALITY_REPORT.md` and older schema/policy text also preserve pre-preprocessing statements such as “no model has been trained” or that duplicate handling is still unresolved; later experiment reports supersede those statements. Use the dated research status and per-run reports as current evidence.

## 3. Completed phases and status

The repository does not contain a canonical numbered phase ledger for Phases 1–5. The mapping below is inferred from the supplied phase names, the documents, and actual files. “Completed” means the stated repository artifact or experiment exists; it does not imply the full MCP-RI research objective has been demonstrated.

| Phase | Objective and actual work | Decisions, artifacts and experiments | Tests/results and remaining limits |
|---|---|---|---|
| 1. Repository audit and research understanding | Research question and candidate datasets documented in the original research document and research/data documents. | `MML-Research-Project (1).md`, `docs/PROJECT_RESEARCH_STATUS.md`, dataset/access docs. Explicit distinction between observed outcomes and cognition is repeated in newer docs. | Research framing is present; not a completed implementation. Many dataset descriptions are candidates, not locally verified assets. |
| 2. Technical architecture and planning | Four-layer architecture, module contracts, data flow, experimental methodology and roadmap specified. | `TECHNICAL_ARCHITECTURE.md`, `MODULE_SPECIFICATIONS.md`, `DATA_FLOW.md`, `IMPLEMENTATION_ROADMAP.md`, experiment/split specs. Initial planner is described as future rule-based work. | Planning only for layers 1–4. No integrated runtime, state store, representation catalog/planner, outcome recorder or application. |
| 3. Dataset investigation and selection | Reviewed task fit and access/label constraints; selected EdNet KT1 plus question contents for response correctness prediction. | Dataset selection/access guides; EdNet chosen for known learner IDs, event order, answer and key. Other datasets remain unacquired candidates. | Decision is implemented as research documentation. No second learner dataset acquired or processed. EdNet is English/TOEIC interaction data and does not support the full multimodal/math-centered claim. |
| 4. EdNet acquisition and validation | Two archives were acquired and metadata recorded. Validation code checks schema, CRC, timestamps, joins, answer keys, missingness and duplicates. | `scripts/acquire_ednet.py`, `scripts/validate_ednet.py`, `src/mcp_ri/ednet_validation.py`, ZIPs and metadata sidecars, quality reports. Local archive SHA-256 values match the recorded values. | Aggregate audit: 784,309 learner files, 95,293,926 interactions, 13,169 question rows, 27,646 blank answers, 4,983 exact duplicate records, 1,314,673 adjacent timestamp ties, no invalid timestamps or unmatched questions. Validation tests passed. |
| 5. Preprocessing and feature engineering | Full processed table created with target derivation, two split protocols, provenance and prior-only histories. | `ednet_preprocessing.py`, `scripts/preprocess_ednet.py`, `scripts/merge_ednet_shards.py`; feature/split/policy docs; processed summary. Duplicate rows were retained and flagged; ties preserve file order; blank-answer events remain but are unlabeled. | 95,293,926 interactions written; 95,266,280 labeled; 27,646 excluded as targets. Leakage whitelist excludes current answer, key, correctness and current elapsed time. Unit tests passed. Historical features correctly update from earlier labeled answers only. |
| 6. Baselines and logistic regression | Three simple baselines plus sparse, incremental SGD logistic model trained and scored. | Seed 2025; deterministic 5% sample of training learners; 3 epochs; 20,000 batch size; L2 alpha 1e-5; optimal SGD learning rate; averaged weights; 12,404 sparse encoded dimensions; `ednet_sgd_logistic.joblib` and fitted JSON encoder. | Full unseen-learner validation only (14,236,525 rows); test unused. Numbers are verified below. No broad hyperparameter search, test estimate, or original-run uncertainty intervals. Saved artifact load was not independently checked in this environment. |
| 7. Random Forest and XGBoost | RF and XGBoost were trained; XGBoost was continued from 300 to 600 boosting rounds. | RF: 24 trees, depth 12, leaf minimum 500, bootstrap 0.5. XGB: hist, depth 6, eta .05, subsampling .8, L2 5, max-bin 128; early-stop subsets from validation. Unique model/report directories preserve results. | All completed tree runs remain behind logistic on most metrics. Both XGB round caps were reached (`best_iteration` 299 and 599), so early stopping did not trigger. No broad hyperparameter search or test evaluation. A Phase 7 run was interrupted before data matrix creation and produced no model/results. |
| 8. Temporal sequence extension (additional phase found) | DKT-style LSTM and SAKT-style causal attention were trained on prior question/correctness sequences. | `train_ednet_sequence_models.py`; deterministic 5% training sample; windows up to 200; 128-d embeddings/hidden dimension; AdamW, early stopping; learner-disjoint early-stop/calibration/report roles; DKT and SAKT checkpoints. | Completed run `phase8-temporal-20261105T073420Z-seed2025` with 11,382,220 matched report transitions / 90,982 learners; no test. SAKT leads several pooled metrics; logistic leads F1. Learner-macro accuracy difference for SAKT vs logistic includes zero. One earlier run failed due to attention-mask dimensions and has no metrics. This is still behavioral prediction, not cognitive estimation. |

## 4. Current machine-learning progress and verified metrics

### Phase 6 claims check

The supplied Phase 6 counts and figures match `results/reports/ednet_logistic_experiment.json`, `results/tables/ednet_validation_metrics.csv`, and the baseline artifact:

| Metric | Stored Phase 6 logistic | Supplied claim | Match |
|---|---:|---:|---|
| Training examples / learners | 3,255,537 / 27,310 | 3,255,537 / 27,310 | Yes |
| Validation examples | 14,236,525 | 14,236,525 | Yes |
| Accuracy | 0.7075149 | 0.7075 | Yes |
| F1 | 0.8021300 | 0.8021 | Yes |
| ROC-AUC | 0.7413215 | 0.7413 | Yes |
| PR-AUC / average precision | 0.8350275 | 0.8350 | Yes |
| Log loss | 0.5647798 | 0.5648 | Yes |
| Brier | 0.1916471 | 0.1916 | Yes |
| ECE (15 equal-width bins) | 0.0357795 | 0.0358 | Yes |

All three supplied baseline results also match: majority accuracy 0.652475 / ROC-AUC .5000; last-response accuracy 0.597415 / ROC-AUC .555617; historical-accuracy accuracy 0.664242 / ROC-AUC .619955. The baseline target prevalence was taken from the full training split. The logistic result is validation evidence under the specified 5% learner sample, not test performance.

### Models actually trained

| Model | Algorithm / inputs / target | Training and evaluation | Validation summary and artifact status |
|---|---|---|---|
| SGD logistic | `SGDClassifier(loss="log_loss")`; sparse one-hot current question/part/tags plus prior event, correctness, accuracy, timing and skill-history fields. Target is correctness of the current submitted answer. | 3,255,537 examples / 27,310 train learners; full unseen-learner validation, 14,236,525 examples. 3 epochs, batch 20k, L2 1e-5, optimal learning rate, averaged SGD. Train 3,887 s; whole run 6,577 s; peak RSS ~1.73 GiB. | Accuracy .7075, F1 .8021, ROC-AUC .7413, AP .8350, log loss .5648, Brier .1916, ECE .0358. Artifact and encoder files exist; load not verified in current environment. |
| Random Forest | 24-tree `RandomForestClassifier`, max depth 12, min leaf 500, max features sqrt, bootstrap/max_samples .5; same sparse features and target. | Same 5% sample; full 14,236,525-row validation. Fit 6.2 s; whole run 2,744 s; peak RSS ~3.63 GiB. | Accuracy .6530, F1 .7899, ROC-AUC .6381, AP .7543, log loss .6290, Brier .2190, ECE .0552. Near-all-positive hard predictions. Model file exists; load not verified here. |
| XGBoost (300) | XGBoost 3.1.3 binary classifier; same sparse feature representation and target. | Same sample; early-stop learner subset 264,908 validation rows; full validation report. Max 300 rounds, best iteration 299; fit 4,139 s; total 8,006 s; peak RSS ~2.65 GiB. | Accuracy .6877, F1 .7948, ROC-AUC .6904, AP .7952, log loss .5926, Brier .2031, ECE .0178. Booster JSON exists; load not verified here. |
| XGBoost continued (600) | Continued prior 300-round booster; no feature change. | Up to 300 additional rounds, patience 30; same early-stop strategy and full validation. Best iteration 599, cap reached; continuation fit 4,364 s, total 7,442 s, peak RSS ~2.61 GiB. | Accuracy .6925, F1 .7968, ROC-AUC .6999, AP .8018, log loss .5872, Brier .2008, ECE .0198. Better than original XGB on most predictive metrics but behind logistic on most. JSON exists; load not verified here. |
| DKT-style | One-layer LSTM over prior question/correctness, predicts current question response. Target remains response correctness. | Same 5% train sample; 3,228,227 transitions from 27,310 learners. Window max 200; 128 dimensions; dropout .2; AdamW lr .001, weight decay 1e-5; max 8 epochs/patience 2; best epoch 2 (4 completed). Fit 76.2 s. | On matched report rows: accuracy .7110, F1 .7992, ROC-AUC .7410, AP .8376, log loss .5585, Brier .1894, ECE .00624. Checkpoint exists; load not verified here. |
| SAKT-style | Causal attention over prior question/correctness interactions, current question as query. | Same training cohort/transitions; 128 dimensions, four heads, causal masking; best epoch 4 (6 completed). Fit 45.4 s. | Accuracy .7133, F1 .7957, ROC-AUC .7464, AP .8411, log loss .5551, Brier .1880, ECE .01318. Best pooled accuracy/ranking/probability-loss among these Phase 8 comparisons; logistic has better F1. Checkpoint exists; load not verified here. |

The Phase 8 comparison uses a report-only cohort of 11,382,220 transitions from 90,982 held-out learners and excludes each learner's first response for every comparator. Its logistic scores therefore differ slightly from full-validation Phase 6 values. SAKT's learner-clustered paired accuracy difference versus logistic is +0.000565, with 95% interval [-0.000623, +0.001858]; this does not show a learner-macro accuracy gain. The sequence and tabular models consume different input representations, so the observed difference is not an architecture-only comparison.

### Tuning, calibration, test and artifacts

- **Hyperparameter tuning:** no broad or systematic search is evidenced. RF/XGB settings are fixed configurations. XGBoost early stopping and sequence-model epoch selection used validation subgroups; XGBoost hit each configured round cap. Phase 8 temperature scaling is a calibration procedure, not a hyperparameter search.
- **Calibration:** Phase 6/7 report metrics and reliability bins/ECE but no post-hoc calibrator. Phase 8 fits scalar temperature on its separate calibration-learner group, then evaluates on report-only learners. This improves selected probability metrics for several models but does not establish robustness or calibration of any cognitive-state estimate.
- **Test partition:** experiment records consistently state `test_partition_used: false`; locked test was not scored.
- **Model loading:** cannot be confirmed during this audit. Current Python lacks `joblib` and `torch`; XGBoost availability is also absent in the active interpreter. Files are present and reports document prior training. JSON syntax/existence is not equivalent to runtime model loading.
- **Other artifacts:** Phase 8 reliability SVG, calibration tables, 1,000 learner-cluster bootstrap summaries and paired comparisons are present. Phase 7 includes grouped feature importance; these are model-use summaries, not causal effects. No independent training log files or test-set evaluation reports exist.

## 5. Dataset and preprocessing audit

### Data inventory and integrity

- Raw KT1 archive: `data/raw/ednet/ednet-kt1.zip`, 1,201,163,816 bytes, SHA-256 `0d13933f90201c5101c7fe8659e44474fa049e3fb93181a8ba6fb3e63267b535`.
- Raw question-content archive: `data/raw/ednet/ednet-content.zip`, 173,976 bytes, SHA-256 `aa910a0436d9dbac0ba232f55e27b37ad8d39da285fcf15f1c1eb5d064be98e7`.
- Processed table: `data/processed/ednet/ednet_kt1_features.csv.gz`, 5,888,235,415 bytes; 95,293,926 data rows plus header, 31 columns. The summary records concatenated gzip shards; the documented decompressed line count and CRC check succeeded in its production workflow.
- Local SHA-256 checks during this audit matched the raw archive metadata. Both raw ZIPs passed `unzip -tq` member CRC checks, and the full processed gzip passed `gzip -t`. Prior preprocessing records also report a matching decompressed row count.

### Data pipeline behavior

`acquire_ednet.py` downloads the official archives, verifies ZIP integrity and records metadata/hashes. `validate_ednet.py` calls the archive inspection implementation for schema, row counts, content mapping, timestamp monotonicity/ties, missing answers, duplicate tuples and target feasibility. `preprocess_ednet.py` streams one learner at a time and writes processed rows; shard merger joins ordered gzip chunks. The feature builder derives the target from submitted answer compared with the joined answer key, preserves source-row order, rejects decreasing timestamps rather than silently sorting, and creates:

- prior logged-event and prior labeled-answer counts;
- cumulative, last-5 and last-10 accuracy and recent trend;
- prior response correctness and prior elapsed time / event gap;
- prior per-skill attempts, correct count and accuracy;
- current question ID, part and expert skill tags.

The current answer, key, correctness and elapsed time are retained as target/provenance columns but excluded by the model feature whitelist. The history state is updated only after writing the current row's features and only when the current row has a valid target. Exact duplicates are retained and flagged, so they also contribute separately to targets/history. Equal timestamps use source row order. Blank-answer events remain in the event stream but do not update correctness history or become targets. The two split columns have distinct purposes: unseen learner assignment by stable learner hash and future-known learner assignment by per-learner target position.

### Actual summary statistics and caveats

784,309 learner CSV files yielded 95,293,926 interactions. 95,266,280 correctness targets were derivable; 27,646 blank answers remained unlabeled. The content table has 13,169 unique questions, all response question IDs join, there are 19,430 rows with missing/sentinel skill tags, 4,983 later exact duplicate rows, 1,314,673 adjacent timestamp ties, and no invalid timestamp or decreasing transition. Maximum interactions for one learner: 40,157. These numbers come from the local quality/preprocessing summaries, not estimates.

Unseen-learner split counts: train 66,898,246 targets / 549,251 learners; validation 14,236,525 / 117,784; test 14,131,509 / 117,269. Future-known counts are per-target chronological partitions; learners may appear in multiple partitions. That protocol is implemented in preprocessing but no reported model experiment uses it.

Leakage controls are meaningful for “question presented, answer not yet submitted” prediction. Current question identity, part and tags are valid only if available at that decision point. Item identity can encode item selection/difficulty structure. Random learner holdout still allows the same questions in training and validation. There is no unseen-item test. Source timestamps are shifted, so absolute calendar interpretation is unsupported. Preserved duplicate targets can overweight repeated records; no deduplication sensitivity experiment is reported. No additional dataset has actually been acquired or implemented.

## 6. Four-layer architecture implementation matrix

Statuses follow the requested vocabulary. “Partially implemented” refers to usable components that do not satisfy the named research function.

| Layer/component | Status | Evidence and boundary |
|---|---|---|
| **Layer 1: Multimodal Evidence Modeling** |||
| EdNet question/response interaction history | PARTIALLY IMPLEMENTED | Streaming ingestion and temporal behavioral feature generation exist. This is one structured modality and does not implement multimodal perception. |
| Language processing | PLANNED ONLY | Research/module documents propose text processing; no text encoder, transcript pipeline or language modality dataset exists. |
| Speech/audio processing | NOT IMPLEMENTED | No audio files, ASR, audio features or alignment. |
| Visual processing | NOT IMPLEMENTED | No learner image/video/visual artifact ingestion or vision model. |
| Handwriting/diagram analysis | NOT IMPLEMENTED | No pen events, handwriting images, diagram parser or relevant local dataset. |
| Temporal alignment across modalities | NOT IMPLEMENTED | EdNet event order and time gaps are handled; no cross-modal alignment or synchronized modality records. |
| Multimodal fusion | NOT IMPLEMENTED | No fusion model, modality masks or fused evidence bundle. |
| Missing-modality handling | PLANNED ONLY | Explicit missingness is discussed in architecture docs; no multimodal model to implement it. |
| Cross-modal agreement/disagreement | NOT IMPLEMENTED | No paired modalities or cross-modal consistency analysis. |
| **Layer 2: Cognitive State Estimation** |||
| Learner response-history representation | PARTIALLY IMPLEMENTED | Counts, accuracies, recent history and DKT/SAKT sequence inputs exist. They represent behavior for response prediction, not a validated cognitive state. |
| Concept grounding | PLANNED ONLY | Item skill tags are attached as item metadata, but no validated concept graph/state grounding or learner concept model exists. |
| Understanding/misconception estimation | NOT IMPLEMENTED | No direct labels, operationalization, estimator or validation. Correctness/retry cannot be substituted for these constructs. |
| Uncertainty estimation | PARTIALLY IMPLEMENTED | Probabilities, Brier/log loss/ECE and Phase 8 scalar calibration exist for correctness prediction. No calibrated cognitive uncertainty or selective state estimator. |
| Temporal state updates | PARTIALLY IMPLEMENTED | Prior response features update over events; no explicit versioned cognitive-state object or state-transition model. |
| Persistent learner context | NOT IMPLEMENTED | Dataset rows group history by learner for experiments; no runtime learner memory/context store. |
| **Layer 3: Representation Intelligence** |||
| Representation catalog/action set | PLANNED ONLY | Specified in architecture/module docs, not implemented in code or data. |
| Decision policy/planner | PLANNED ONLY | Docs recommend inspectable rules and diagnostic fallback; no executable selection policy. |
| Text/visual/spatial/symbolic/interactive/simulation outputs | NOT IMPLEMENTED | No representation generation or transformation components. |
| Diagnostic questions/contextual diversions | PLANNED ONLY | Research proposal and module design only; no action flow or continuity logic. |
| **Layer 4: Outcome and State Update** |||
| Later response outcomes | PARTIALLY IMPLEMENTED | EdNet logs outcomes and prior-event features; they are not linked to a representation intervention. |
| Post-intervention exposure/outcome evaluation | NOT IMPLEMENTED | No intervention/action assignment, exposure or follow-up treatment record. |
| Learner feedback | NOT IMPLEMENTED | No learner self-report or feedback source. |
| Cognitive-state update | NOT IMPLEMENTED | No state estimator/store/versioning. |
| Teaching trajectory continuity / branch create-resume | PLANNED ONLY | A core research motivation and data-flow design; no branch, parent pointer, return point or resume implementation. |

No layer should be marked complete. No end-to-end integration exists.

## 7. Testing and software quality

### Test execution

Command run: `python3 -m unittest discover -s tests -v` (read-only; no test files or project artifacts changed).

- 15 test cases passed across data validation, preprocessing and shard merging.
- `test_ednet_ml_pipeline` was skipped because training requirements were not installed.
- `test_ednet_advanced_models` failed to import because `joblib` is unavailable.
- `test_ednet_sequence_models` failed to import because `torch` is unavailable.
- Overall unittest discovery exited with status 1 because of these two import errors.

Test coverage includes ZIP corruption detection, schema and timestamp parsing, answer-key joins, duplicate/tie behavior, leakage-guard invariance under current answer changes, history isolation, split reproducibility, temporal split boundaries, shard merge order and (in the unavailable dependency suites) model checkpoint/logit and causal future-response checks. Tests do not establish full pipeline reproducibility, end-to-end serving, data-quality statistics on every run, production robustness, cognition validity or intervention benefit.

### Quality observations

- **Strengths:** streaming preprocessing and training; explicit feature whitelist; deterministic learner hash sample and split; training-only categorical/scaling encoder; current-target leakage checks; reports preserve settings, versions, data hashes and run status; exceptions are captured as failed run metadata in training scripts.
- **Dependencies:** environment files exist but they do not reproduce the original full environment by themselves: the deep-learning requirement is a CUDA-specific PyTorch wheel. The current environment lacks key dependencies, preventing artifact-load verification and full test discovery. The reports include prior environment versions.
- **Reproducibility:** seeds and split procedures are recorded; one trained seed/sample per principal comparison is insufficient to measure training-seed variation. There is no committed lockfile, container definition, or automated end-to-end data-to-model reproduction check. Existing absolute artifact paths in reports are host-specific, although scripts expose data/output roots.
- **Memory/runtime:** the processor is per-learner streaming, and matrices are sparse. Large validation evaluation materializes probability/label arrays in memory in some scripts. Recorded peaks range around 1.7–3.6 GiB for tabular runs and 4.6 GiB for the sequence run.
- **Leakage/evaluation:** learner-level splits and feature guards reduce obvious leakage. Validation was used for early stopping and epoch selection in some models. Test remains reserved. Current item metadata's point-in-time availability is an explicit condition. No second domain, unseen-item split, temporal known-learner model result, or subgroup/fairness report exists.
- **Logging:** progress is printed; structured run/report JSON exists. There are no standalone persistent console/training logs. Failed/interrupted run records are retained.
- **Documentation consistency:** older data quality/schema/preprocessing text says modeling has not yet occurred; newer reports supersede it. README omits Phase 8 and does not enumerate all scripts. Phase 7 comparison docs clearly state test was unused and tree configurations were not an exhaustive search.
- **Code structure:** utilities are mostly direct scripts and one package; no installed package metadata or inference/application layer. This is acceptable for research scripts but does not yet provide a stable user-facing model API.

## 8. Completed research contributions and evidence boundaries

1. Formalized a testable research question connecting evidence, state, representation choices and outcomes, while documenting that no identified public dataset covers the full loop.
2. Selected a feasible initial observed target and precisely separated response correctness from cognitive constructs.
3. Acquired, hashed, schema-checked and quality-audited EdNet KT1 and question content. Created a large reproducible processed snapshot with provenance and two learner-aware split protocols.
4. Implemented leakage-aware historical feature engineering and unit tests for important chronology, split and target-boundary rules.
5. Experimentally demonstrated next-response correctness signal on held-out learners with several baselines, logistic and tree models, including calibration reporting.
6. Trained DKT and SAKT-style sequence models and compared them on a matched held-out validation cohort with learner-cluster bootstrap uncertainty and separate temperature calibration.

The evidence supports behavioral prediction on this sampled EdNet protocol only. It does not demonstrate multimodal evidence integration, cognitive-state estimation, misconception/mismatch detection, better representation selection, a persistent teaching trajectory, or improved learning outcomes. Software implementation and scientific construct validation remain separate.

## 9. Prioritized unfinished work

The items below are future work recommendations, not work performed by this audit. Inputs and outputs describe the minimum useful contracts; evaluation must follow the target actually defined.

### A. Immediate next steps

1. **Freeze experiment protocol before using the locked test.** Required because the current validation has guided XGBoost/sequence epoch selection and calibration choices. Specify primary estimand (response-weighted or learner-weighted), primary metric, model set, calibration and thresholds; dependency: existing data, saved models and reports. Input: frozen artifacts and test split; output: one test result table and immutable protocol. Evaluate once on test, report learner-clustered uncertainty, and do not tune on test.
2. **Restore a reproducible model environment and verify saved inference.** Required to substantiate that artifacts can be used, not merely that training reports exist. Dependencies: Python 3.12 and compatible sklearn/XGBoost/PyTorch plus CUDA or CPU-capable torch. Inputs: encoder and model files plus a small synthetic or held-out feature batch; outputs: loaded models and probabilities. Evaluate load round-trip, deterministic predictions, schema compatibility and documented CPU/GPU behavior. Do not retrain as part of this audit.
3. **Resolve stale documentation and establish one current status index.** Needed to prevent obsolete “not trained” text from contradicting Phase 6–8. Inputs: existing phase/run reports; output: consistent pointers/status. Evaluate by cross-checking every status/metric against machine-readable reports.
4. **Run predeclared sensitivity/robustness checks before broader claims.** Needed because current results are single-sample/single-seed and preserve duplicate events. Dependencies: available processed table and chosen protocol. Inputs: fixed split and duplicate policy variants; outputs: matched metric and uncertainty report. Evaluate on validation first; keep test closed until all decisions freeze.

### B. Remaining machine-learning experiments

- **Matched-input model ablation:** needed to separate architecture from feature advantage in Phase 8. Implement a shared input representation for logistic/tree/sequence variants (or carefully defined sequence-derived aggregates). Dependencies: current EdNet pipeline and train-only vocab. Inputs: same learner rows and item/history fields; outputs: comparable predictions. Evaluate with same cohort, row- and learner-weighted metrics, multiple seeds, bootstrap intervals and calibration.
- **Predeclared tuning and training-scale study:** needed because current 5% sample and fixed settings do not establish full-scale performance or optimal configurations. Inputs: train-only learners and a bounded compute budget; outputs: selected model settings and retrained baselines. Train every comparator on the same learner set; validate using separate learners; evaluate locked test only after freeze.
- **Duplicate and item generalization sensitivity:** needed because duplicate copies receive extra weight and unseen learners still share questions. Inputs: retained/deduplicated variants and an item-held-out split. Outputs: sensitivity report. Evaluate whether conclusions persist under both duplicate policies and unseen-item generalization.
- **Temporal known-learner evaluation:** needed for a different deployment setting where prior learner history is available. Inputs: existing `split_future_known_learner`, history strictly before each target; outputs: future-period prediction. Evaluate against per-learner temporal baseline, time-forward metrics and learner-clustered intervals. Do not mix this estimand with unseen-learner scores.

### C. Temporal modelling

- **Stability and drift:** needed to determine if sequence gains survive seed/snapshot/time changes. Requires repeated training seeds and, ideally, an updated or future period. Inputs: ordered histories and item IDs; outputs: stable temporal predictions. Evaluate multi-seed variance, calibration drift and performance by history length/time.
- **Longer-context/state design:** current windows cap context at 200 and reset hidden state at boundaries. If long-range dependencies matter, implement state carry or compare window lengths. Requires compute and a declared temporal hypothesis. Input: longer event sequences; output: next-response prediction/state features. Evaluate with matched training budget and leakage-safe held-out learners/time.

### D. Multimodal perception

- **Obtain a suitable multimodal dataset or collect one under approved protocol.** Required for language/voice/visual/pen evidence. Dependencies: access terms, license, consent/ethics if new data, verified schema/IDs/time alignment. Inputs: synchronized text/audio/artifact/events and labels; outputs: modality-specific records with provenance and availability masks. Evaluate alignment quality, label coverage and each modality on the same eligible cohort before fusion.
- **Build modality encoders, missing-modality and fusion baselines.** Needed to test whether modalities add information. Requires verified media and a common, documented target. Inputs: timestamped modalities and masks; outputs: unimodal and late-fusion predictions/evidence. Evaluate matched ablations, robustness when modalities are absent, calibration and participant-held-out uncertainty. Engagement/correctness must retain their actual construct names.
- **Cross-modal agreement/disagreement analysis.** Needed for the stated mismatch hypothesis. Requires paired language and written/visual work plus an independently specified mismatch label. Inputs: aligned utterance/artifact pairs; output: disagreement score/evidence. Evaluate against blinded human annotation with inter-rater agreement and held-out participant performance.

### E. Cognitive-state modelling

- **Operationalize state constructs and collect valid labels.** Required because response correctness is not understanding, confusion or misconception. Dependencies: construct definitions, annotation/self-report protocol, trained raters or validated instruments, ethics/consent as applicable. Inputs: task/concept context and evidence with independent state labels; outputs: construct-specific target table. Evaluate label reliability, coverage, construct validity and subgroup limitations.
- **Implement a calibrated, evidence-linked state estimator.** Requires repeated valid labels and a temporal study design. Inputs: evidence bundles, concept IDs and prior observations; outputs: per-construct estimates, uncertainty/abstention, source evidence and unknown states. Evaluate grouped/time-forward discrimination or regression, calibration, selective risk/coverage and external/participant-held-out validity.
- **Persistent learner context/versioning.** Required for evolving-state claims. Dependencies: data schema, privacy/retention policy and validated state output. Inputs: observations and prior state version; outputs: append-only state history and new estimate. Evaluate state-transition auditability, no overwrite, provenance and temporal leakage tests.

### F. Representation Intelligence

- **Create a content-linked representation catalog.** Needed before a policy can choose among actual alternatives. Dependencies: constrained subject/concept, authored text/visual/spatial/symbolic/interactive/simulation assets, content metadata. Inputs: concept, prerequisites, asset/action affordances; outputs: available representation options with identifiers and expected observation. Evaluate coverage, correctness and concept alignment with expert review.
- **Implement an inspectable rule-based planner and diagnostic fallback.** Required prototype before learned selection. Dependencies: catalog, context, explicit constraints and uncertainty interface; inputs: concept/goal, current frame, learner request/state estimate, available options and branch pointer; outputs: plan/action, rationale/evidence IDs, follow-up and return point. Evaluate feasibility, rationale completeness, diagnostic utility, safety/teacher review and interruption-resumption continuity. Do not claim learning benefit from workflow tests.
- **Add learned action ranking only with action/outcome data.** Requires logged availability, exposure, assignment, context and follow-up; preferably randomized/counterbalanced assignment. Inputs: context and candidate actions; outputs: ranked plan/value with uncertainty. Evaluate with valid causal/offline policy methodology and then prospective comparison against rules; do not imitate confounded logged choices as a validated policy.

### G. Outcome and state updates

- **Record exposure, usage, feedback and post-action outcomes.** Needed to distinguish what was offered, what was used and what helped. Dependencies: planner/action IDs, concept-aligned outcome instrument and consent where applicable. Inputs: plan, actual exposure/usage, response and learner feedback; outputs: linked outcome record and evidence event. Evaluate completion, missingness, timing and provenance.
- **Version state after outcomes and preserve branches.** Required for trajectory continuity. Dependencies: persistent state store and branch/return schema. Inputs: prior state, action, exposure and follow-up; outputs: new immutable state version and resume/replan pointer. Evaluate branch integrity, return-to-original-goal success, audit traces and state update quality against independent review.
- **Evaluate intervention benefit prospectively.** Requires prespecified primary outcome, adequate power and ethical assignment. Inputs: eligible learners, available representations, assignment and baseline/follow-up measures; outputs: causal estimate of representation condition effect. Evaluate with randomized/counterbalanced design or a defensible causal identification strategy, confidence intervals and attrition analysis.

### H. End-to-end integration

- **Implement interfaces between ingestion, evidence, state, planner and outcome records.** Needed to turn module specifications into a running prototype. Dependencies: stable event/evidence/state/plan/outcome schemas, consent/access rules and one constrained domain. Inputs: a learner event and teaching context; outputs: state/evidence record, plan, observed outcome and next version. Evaluate end-to-end traceability, latency, failure/missing-modality behavior, state provenance and branch-resumption integration tests.
- **Provide a serving/inference API and application workflow.** No app exists today. Inputs: approved context/events; outputs: inspectable next action and feedback capture. Evaluate usability with teachers/learners, error handling, privacy controls and safe fallback; keep research evaluation distinct from product usability.

### I. Research evaluation and final reporting

- **Build a construct-valid evaluation program.** Required to test the central MCP-RI hypothesis. Dependencies: aligned multimodal data, state labels, action options and prospective outcomes. Inputs: full evidence-to-action trajectory; outputs: component and end-to-end estimates. Compare unimodal/multimodal, static/temporal, heuristic/state-aware and mastery-only baselines on matched cohorts; report calibration, subgroup limits and uncertainty.
- **Replication and external validity.** Required before general claims. Use a second domain/population or verified benchmark with distinct data access. Inputs: frozen models/protocol; outputs: dataset-specific results. Evaluate transfer separately, without pooling mismatched targets or treating dataset size as construct validity.
- **Final scientific report.** Required to state what the project established. Include preregistered hypotheses, deviations, data/license and ethics, splits, all attempted runs including failures, full metrics/uncertainty, negative results and reproducibility artifacts. Distinguish predictive performance, construct validity and intervention effects.

## 10. Recommended roadmap

1. **Evidence freeze:** resolve documentation conflicts, restore the pinned environment, load-check artifacts, choose estimand/metric and freeze all current EdNet model decisions.
2. **Complete EdNet validation study:** predeclare any sensitivity and training-scale work; retrain comparisons only if authorized as a later phase; evaluate the reserved test exactly once after freeze. Keep it explicitly a behavioral component study.
3. **Select one constrained multimodal domain and access route:** verify license, files, synchronization, participant structure and annotations before any acquisition. If no existing dataset supports the required constructs, design an ethically approved data collection protocol.
4. **Establish modality and construct baselines:** define independent labels, evaluate each modality and late fusion, and test calibration/missingness on matched learner-held-out cohorts.
5. **Build the smallest auditable MCP-RI prototype:** content catalog, rule-based representation plan, uncertainty fallback, branch/return pointer, exposure/outcome recorder and versioned state record. Use human review and avoid learned policy claims initially.
6. **Prospective evaluation:** predefine outcomes and compare representation conditions under a credible assignment design. Assess component validity and learning benefit separately.
7. **Expand only after evidence gates:** train learned action policies only after adequate action-outcome coverage, replication and prospective safety/benefit checks.

## 11. Final audit conclusion

What is demonstrably built and experimentally exercised is an EdNet response-data pipeline and a series of response-correctness predictors, including temporal sequence models. The recorded Phase 6 numbers and supplied baseline figures are accurate. Phase 7 is completed for RF, XGBoost 300 rounds and XGBoost continuation to 600 rounds; the latter hit its cap. Phase 8 is completed for DKT and SAKT-style models, with an earlier failed run retained. All completed runs use validation evidence; the locked test partition remains untouched.

The project has not built or validated the four-layer multimodal cognitive system described in its research objective. Its core research contribution remains a proposal with substantial data/model infrastructure for one behavioral component. No cognitive-state, multimodal-fusion, representation-selection, branch-resumption, or intervention-benefit claim is supported by current local data or experiments.

## Phase 9 addendum — 6 November 2026

Since the repository audit above, Phase 9 implemented a replayable behavioral learner-state summary over the existing EdNet stream. This updates the audit's prior statement that learner-state persistence was not implemented: a per-learner accumulator and versioned JSON state now exist, but no persistent database or validated cognitive state exists.

- Implementation: `src/mcp_ri/learner_state/`, `scripts/learner_state/build_and_evaluate.py`, `schemas/learner_state_v1.schema.json`.
- Full validation run: `results/reports/phase9-learner-state-20261106T081823Z/`.
- Generated 117,785 validation learner states and 3,897,566 per-skill states from 14,241,124 validation interaction rows, including 4,599 unlabeled interactions. One state is for a validation-hash learner with no labeled response.
- All 117,785 generated states passed the versioned JSON Schema and count/numeric checks. The process scanned the 95.29-million-row input once, took 2,246 seconds and peaked at 349,852 KiB RSS. No test state or model prediction was produced.
- The Phase 9 focused suite passes 20 tests. Full repository unittest discovery still cannot import two existing ML test modules because `joblib` and `torch` are absent from the current Python environment; one existing ML module is skipped for missing training requirements.
- Methodology and descriptive results: `LEARNER_STATE_ARCHITECTURE.md`, `LEARNER_STATE_METHODOLOGY.md`, `LEARNER_STATE_EXPERIMENTS.md`, and `LEARNER_STATE_EVALUATION.md`.

Phase 9 advances the Layer 2 data structure and temporal replay foundation. Its outcomes, trends and flags remain summaries of correctness behavior; direct cognitive-state accuracy is unavailable.

## Phases 10–12 addendum — 6 November 2026

The audit conclusion above describes the state before Phases 10–12 and is superseded by these implementation updates. The research limits still apply: no direct cognitive labels, real multimodal learner content, representation assignment data, or learning-benefit outcomes are available.

- **Phase 10:** `src/mcp_ri/evidence/` implements versioned evidence records, provenance, grouping/alignment and adapters. Only interaction and derived temporal evidence are real EdNet learner data; text/audio/visual adapter coverage is synthetic.
- **Phase 11:** `src/mcp_ri/cognitive_state/` adds a separate provisional estimator over complete Phase 9/10 prefixes. The bounded validation run produced 184 snapshots for 100 learners. This is traceability/rule coverage, not cognitive accuracy.
- **Phase 12:** `src/mcp_ri/representation/` adds a versioned taxonomy and plan schema, explicit availability registry, rule trace, metadata-only EdNet grounding and append-only plan history. The bounded run created 1,910 plans from the Phase 11 validation snapshots; 100% linked to source evidence in the independent source check, and all 717 temporal links preserved teaching context. The registry has no implemented delivery provider, so no representation was selected for execution. This is engineering evaluation, not educational effectiveness.
- **Current environment:** Python 3.12.3 has `jsonschema`, NumPy and SciPy; PyTorch and `joblib` are absent. Phase-specific focused test results are in `REPRESENTATION_EVALUATION.md` and the earlier phase reports. The full repository suite still has optional dependency import errors for existing ML tests.
