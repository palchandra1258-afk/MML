# F6 — Research and model evaluation dashboard

## Architecture and data access

The `/evaluation` route and `/research` overview both render `ResearchEvaluationPage`, backed by the typed catalog in `lib/research/catalog.ts` and the committed aggregate snapshot in `lib/research/evaluation-snapshot.json`. The OpenAPI contract has no model-evaluation, experiment-catalog, or report-file operation. F6 therefore uses a versioned, allowlisted snapshot; it adds no API path, does not read the repository filesystem from the browser, and does not treat API health as research evidence. The page labels the snapshot date and source type.

Only aggregate validation metrics, calibration bins, run metadata, and aggregate Phase 9–13 summaries are included. Learner-level JSONL exports and model checkpoints are not loaded into the application bundle. Source references are repository-relative labels in the report inventory and detail panels. The UI does not create arbitrary file URLs or serve server paths. Selecting a run opens its metadata and can navigate to the matching saved metric cohort.

The report inventory records the distinction between `measured_experimental_result`, `engineering_validation`, `synthetic_evaluation`, `unvalidated_hypothesis`, and `not_evaluated`. Saved checkpoints and methodology documents are not counted as independent measured experiments.

## Research artifact audit

The audit inspected `results/`, `models/`, `data/`, `scripts/`, `docs/`, `shared/api-contracts/openapi.json`, and the current frontend API services. It checked the report, metric, calibration, configuration, split, and evaluation metadata files before selecting fields for the snapshot.

| Artifact source | What it contains | Dashboard treatment |
|---|---|---|
| `results/reports/ednet_logistic_experiment.json`; `results/tables/ednet_validation_metrics.csv`; `results/tables/ednet_validation_calibration.csv` | Phase 6 baseline and SGD logistic result, run configuration, metric and bin values | Measured prediction evaluation; included |
| `results/reports/phase7-20261104T100155Z-seed2025/run.json` | Interrupted before matrix construction; no training or results | Not evaluated; listed but excluded from result counts |
| `results/reports/phase7-20261104T100506Z-seed2025/` | XGBoost 300-round results, calibration, and grouped feature importance | Measured prediction evaluation; included |
| `results/reports/phase7-20261104T121919Z-seed2025/` | Random Forest results, calibration, and grouped feature importance | Measured prediction evaluation; included |
| `results/reports/phase7-xgb-resume-20261105T040130Z-seed2025/` | XGBoost continuation to 600 rounds, metrics, and calibration | Measured prediction evaluation; included |
| `results/reports/phase8-temporal-20261105T070210Z-seed2025/run.json` | Failed sequence-model attempt; attention-mask error before results | Not evaluated; listed without scores |
| `results/reports/phase8-temporal-20261105T073420Z-seed2025/` | Matched DKT/SAKT and comparator scores, confusion matrices, raw/scaled bins, and paired learner bootstrap | Measured prediction evaluation; included |
| `results/figures/phase7_reliability_20261104.svg`; `results/figures/phase7_reliability_20261105.svg`; `results/figures/phase8-temporal-20261105T073420Z-seed2025_reliability.svg` | Saved reliability diagrams | Checked against available bin data; the dashboard plots the aggregate bin values |
| `results/tables/phase7_advanced_comparison_20261104.csv`; `results/tables/phase7_advanced_comparison_20261105.csv`; `results/tables/phase7_calibration_bins_*.csv` | Consolidated Phase 7 model comparisons and calibration | Cross-checked against run-level reports |
| `results/reports/phase9-learner-state-20261106T081823Z/evaluation.json` | Validation-only descriptive behavioral-state aggregate | Engineering validation; included |
| `results/reports/phase10-evidence-20261106T101321Z/public_summary.json` | Bounded evidence schema/provenance counts | Engineering validation; included as data coverage context |
| `results/reports/phase11-cognitive-state-20261106T104113Z/evaluation.json` | Bounded cognitive rule and category counts | Engineering validation only; included with explicit ground-truth limitation |
| `results/reports/phase12-representation-20261106T112420Z/{build_report,evaluation}.json` | Latest bounded plan build and traceability checks | Engineering validation; included |
| `results/reports/phase13-trajectory-20261111T040954Z/{build_report,evaluation,history_validation}.json` | Final bounded trajectory and history validation | Engineering validation; included |
| Earlier Phase 12/13 run directories | Additional saved runs, including larger and repeated samples | Inventoried; selected run is identified in the dashboard rather than summing duplicate run outputs |
| `models/baselines/`, `models/trained/`, `models/preprocessing/` | Baseline definition, fitted encoder, and trained checkpoints | Inspected for metadata; checkpoints do not add result rows |
| `data/processed/ednet/ednet_preprocessing_summary.json`; `data/processed/ednet/ednet_quality_summary.json` | Dataset sizes, split counts, missingness and quality checks | Inspected for sample/split context; raw/processed interaction tables are not loaded by the browser |
| `scripts/training/`, `scripts/learner_state/`, `scripts/cognitive_state/`, `scripts/representation/`, `scripts/trajectory/` | Training/evaluation protocol implementation | Read to confirm target, split, calibration and validation semantics |
| `docs/MODEL_EVALUATION_REPORT.md`, `docs/BASELINE_EXPERIMENTS.md`, `docs/ADVANCED_MODEL_COMPARISON.md`, `docs/PHASE8_CALIBRATION_ANALYSIS.md`, `docs/PHASE8_SEQUENCE_MODEL_COMPARISON.md` | Prediction protocol, metric interpretation and limitations | Used to annotate comparisons and model inputs |
| Phase 9–14 evaluation/methodology documents | Construction, ground-truth limits, plan validation, trajectory rules and synthetic API tests | Used to label engineering and synthetic evidence separately |

The experiment inventory contains five runs with saved prediction metrics: Phase 6 logistic/baselines, Phase 7 XGBoost 300, Phase 7 Random Forest, the resumed XGBoost 600 run, and the completed Phase 8 matched comparison. It also lists one interrupted Phase 7 setup and one failed Phase 8 attempt; neither is counted as an evaluated run. There is one prediction dataset and six model families when the three baseline variants are grouped together.

## Prediction results and metric comparison

The full unseen-learner validation cohort contains 14,236,525 labeled responses from 117,784 learners. It supports seven compared variants: majority/prevalence, last-response persistence, historical-accuracy persistence, SGD logistic regression, Random Forest, XGBoost 300, and XGBoost continued to 600 rounds. The full cohort source is the Phase 7 continuation report; the Random Forest row preserves its own report source. These reports share the same target, validation learner split, sample denominator, and fixed 0.5 classification threshold.

The Phase 8 report-only cohort contains 11,382,220 matched next-response transitions from 90,982 learners. It includes the same three baselines, logistic, Random Forest, XGBoost 600, DKT, and SAKT-style. The sequence models omit each learner's first response. Comparisons are restricted to one selected cohort. The Phase 8 report compares different model-and-input pipelines: tabular models use engineered item/history features while DKT/SAKT use question identity and earlier correctness sequences. This is not an architecture-only ablation, and the dashboard does not produce an overall model ranking.

Available scalar metrics are accuracy, precision, recall, F1, ROC-AUC, PR-AUC/average precision, log loss, Brier score, and equal-width ECE. The detailed metric panel defines each measure and reads values directly from the saved metric records. Missing values render as unavailable. Confusion matrices are displayed where saved in the full validation run JSON and Phase 8 experiment JSON; no matrix is computed from incomplete metrics.

Both evaluated cohorts use EdNet KT1 and predict submitted-answer correctness, a behavioral outcome. The held-out test partition has not been evaluated and is not presented as a development option. Phase 8 paired learner bootstrap intervals are available only for selected DKT/SAKT differences on accuracy, log loss, and Brier score; Phase 6/7 pooled metrics have no learner-clustered intervals. The bootstrap is conditional on the trained run and does not account for training-seed or sample variation.

## Calibration analysis

Calibration views consume the saved 15-bin `mean_probability`, `observed_positive_rate`, and `count` values. Empty bins are omitted from the plotted data; when there are no occupied bins, the page shows an explicit unavailable state. The diagonal is a mathematical perfect-calibration reference, not an observed series. The chart labels the probability and observed-frequency axes and has an accessible title/description and per-point bin details.

The Phase 8 view offers raw and temperature-scaled records. The temperature was fitted on a separate learner-disjoint calibration cohort (1,324,710 transitions from 11,728 learners) and applied to the report-only cohort; it was not fit on report-only labels. Brier, ECE, and log loss are shown beside the saved reliability bins. Accuracy and ranking metrics remain unchanged under temperature scaling. A low ECE does not by itself show useful ranking or calibration under future distribution shift.

## Behavioral, cognitive, representation and trajectory coverage

### Phase 9 behavioral learner state

The validation-only stream contains 117,785 learner snapshots over 14,241,124 interactions, including 14,236,525 labeled responses and 4,599 unlabeled events. All 117,785 state records passed the documented schema check. No model predictions were available, and confidence intervals are not reported in the aggregate evaluation. The page shows recent/historical behavior and evidence-sufficiency tiers as descriptive summaries; these do not measure true knowledge.

### Phase 10 evidence coverage

The public aggregate report has 1,000 EdNet interaction records from 1,000 learners, 1,000 schema/provenance checks, 1,000 singleton groups, and zero alignment candidates. This is a bounded interaction sample, not a real text/audio/visual learner-media evaluation.

### Phase 11 cognitive-state coverage

The bounded sample contains 184 snapshots from the first 100 validation learners in processed source order. It is a coverage smoke sample, not a random population estimate. Saved categories and hypotheses are provisional rule outputs. The separate validation report states that the 184 records and version links were checked; the aggregate does not report a separate evidence-reference count or diagnostic-recommendation count. EdNet supplies no validated cognitive-state ground-truth labels, so cognitive accuracy, misconception-detection accuracy, diagnosis effectiveness, and calibration are not established. Multimodal fixtures are synthetic.

### Phase 12 representation planning

The selected final bounded report built 1,910 plans from 184 Phase 11 snapshots. All eight capabilities were unavailable; zero plans selected a representation. It recorded 1,879 diagnostic-evidence requests, 14 additional-evidence requests, 17 deferrals, 1,910 cognitive-state reference matches, 1,910 evidence-reference matches, and 717/717 temporal plan links preserving context. These results validate plan construction, capability gating, and traceability. They do not measure delivery or learning effect.

### Phase 13 trajectory orchestration

The selected run created 100 trajectories for 55 learners. It validated 100/100 observed transitions, rejected 44/44 illegal edges, reconstructed 300/300 events and 200 versions, replayed 100/100 decisions identically, and passed 100/100 evidence-reference checks. It created zero diversions because the real dependency registry was empty and all 100 decisions requested more evidence. Diversion-only rates have a zero denominator and remain unavailable. Synthetic tests exercise nonzero diversion/resumption paths, but the bounded real-data sample does not establish those outcomes under real dependency edges or learner benefit.

## Missing artifacts and scientific limits

- No model-evaluation or report-catalog endpoint is present in OpenAPI; snapshot values are not live API results.
- No independent locked-test prediction result is published.
- There are no cognitive ground-truth labels, cognitive accuracy/calibration metrics, validated misconception labels, or diagnosis-effectiveness outcomes.
- No representation exposure, delivery, controlled comparison, or post-intervention learning outcomes are available.
- No real dependency registry or real-data diversion/resumption outcome is available.
- Real learner text, audio and visual evidence are not represented in the saved EdNet evaluation cohort.
- Experiment configuration or hypothesis fields that were absent from a report are labeled as unrecorded; no settings are inferred from a model checkpoint.
- No global aggregate count is computed by summing repeated report files. The dashboard selects the declared cohort/run and documents duplicate or superseded artifacts.

## Testing and validation

- ESLint: passed.
- `npm run test:api`: passed, 53 total tests (18 F6 research tests); 0 failed.
- `npx tsc --noEmit`: passed.
- `npm run build`: passed.
- `git diff --check`: passed.
- Browser-level visual/interaction testing was not performed; no browser test setup is installed. The reliability chart and responsive navigation receive source/unit coverage.

## Remaining dependency

A versioned report API or a maintained artifact publication pipeline would allow server-curated updates without refreshing the frontend snapshot by hand. This phase does not create that backend capability. F7 is the trajectory, diversion, and resumption experience; it is not started here.
