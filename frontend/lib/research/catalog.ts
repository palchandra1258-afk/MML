import snapshotJson from "./evaluation-snapshot.json";

export type ResultClassification = "measured_experimental_result" | "engineering_validation" | "synthetic_evaluation" | "unvalidated_hypothesis" | "not_evaluated";
export type MetricKey = "accuracy" | "precision" | "recall" | "f1" | "rocAuc" | "prAuc" | "logLoss" | "brierScore" | "ece";
export type CalibrationVariant = "raw" | "temperature_scaled";

export interface CalibrationBin {
  lower: number | null;
  upper: number | null;
  count: number;
  meanProbability: number | null;
  observedPositiveRate: number | null;
}

export interface ModelResult {
  cohortId?: string;
  runId?: string;
  evaluatedAt?: string;
  modelId: string;
  family: string;
  label: string;
  variant: string;
  metrics?: Partial<Record<MetricKey, number | null>>;
  metricVariants?: Partial<Record<CalibrationVariant, Partial<Record<MetricKey, number | null>>>>;
  examples: number;
  learners: number;
  confusionMatrix?: number[][] | null;
  confusionMatrixSource?: string | null;
  calibrationBins?: CalibrationBin[] | Partial<Record<CalibrationVariant, CalibrationBin[]>>;
  calibrationMethod: string;
  temperature: number | null;
  resultClassification: ResultClassification;
  source: string;
  metricsSource: string;
  calibrationSource: string;
}

export interface EvaluationCohort {
  id: string;
  label: string;
  dataset: string;
  target: string;
  split: string;
  protocol: string;
  examples: number;
  learners: number;
  classification: ResultClassification;
  metricsSource: string;
  calibrationSource: string;
  source: string;
  models: ModelResult[];
  modelMetricsSources?: string;
}

export interface ArtifactInventoryItem {
  path: string;
  type: string;
  classification: ResultClassification;
  included: boolean;
}

export interface PhaseValidation {
  id: string;
  status: string;
  classification: ResultClassification;
  source: string;
  report: string;
  [key: string]: unknown;
}

interface ResearchSnapshot {
  snapshotDate: string;
  snapshotType: string;
  cohorts: EvaluationCohort[];
  phase9: PhaseValidation;
  phase10: PhaseValidation;
  phase11: PhaseValidation;
  phase12: PhaseValidation;
  phase13: PhaseValidation;
  artifactInventory: ArtifactInventoryItem[];
  missingArtifacts: string[];
}

export interface ExperimentRecord {
  id: string;
  runId?: string;
  name: string;
  phase: string;
  status: "complete" | "interrupted" | "failed";
  timestamp?: string;
  savedResults: boolean;
  classification: ResultClassification;
  objective: string;
  hypothesis: string;
  dataset: string;
  split: string;
  target: string;
  evaluationMethod: string;
  configuration: string[];
  resultSource: string;
  sourceReport: string;
  limitations: string[];
}

const snapshot = snapshotJson as ResearchSnapshot;

export const evaluationCohorts = snapshot.cohorts;
export const artifactInventory = snapshot.artifactInventory;
export const missingArtifacts = snapshot.missingArtifacts;
export const phaseValidations = [snapshot.phase9, snapshot.phase10, snapshot.phase11, snapshot.phase12, snapshot.phase13];
export const snapshotDate = snapshot.snapshotDate;
export const snapshotType = snapshot.snapshotType;

export const experiments: ExperimentRecord[] = [
  {
    id: "ednet-logistic-validation",
    name: "EdNet KT1 logistic and baseline evaluation",
    phase: "Phase 6",
    status: "complete",
    timestamp: "2026-11-04T08:06:23.828965Z",
    savedResults: true,
    classification: "measured_experimental_result",
    objective: "Predict correctness of the next submitted answer for unseen learners.",
    hypothesis: "No formal hypothesis is recorded in the saved report.",
    dataset: "EdNet KT1",
    split: "Unseen-learner validation; 14,236,525 labeled examples from 117,784 validation learners.",
    target: "Submitted-answer correctness; behavioral outcome, not a direct cognitive measure.",
    evaluationMethod: "Fixed 0.5 threshold; pooled validation metrics; 15 equal-width ECE bins. Test partition not used.",
    configuration: ["SGDClassifier with logistic loss; deterministic 5% of training learners; seed 2025.", "Three epochs; batch size 20,000; L2 alpha 1e-5; 12,404 encoded features."],
    resultSource: "results/reports/ednet_logistic_experiment.json; results/tables/ednet_validation_metrics.csv; results/tables/ednet_validation_calibration.csv",
    sourceReport: "docs/MODEL_EVALUATION_REPORT.md; docs/BASELINE_EXPERIMENTS.md; docs/LOGISTIC_REGRESSION_EXPERIMENT.md",
    limitations: ["A sampled training learner set and one unseen-learner validation split were used.", "No test-set evaluation, learner bootstrap interval, or post-hoc calibration was reported."],
  },
  {
    id: "phase7-interrupted-setup",
    runId: "phase7-20261104T100155Z-seed2025",
    name: "Interrupted Phase 7 setup",
    phase: "Phase 7",
    status: "interrupted",
    timestamp: "2026-11-04T10:05:00Z",
    savedResults: false,
    classification: "not_evaluated",
    objective: "Prepare the existing training sample for advanced model evaluation.",
    hypothesis: "No model was trained; there is no evaluated hypothesis.",
    dataset: "EdNet KT1",
    split: "Training setup stopped before matrix construction.",
    target: "Submitted-answer correctness; behavioral outcome.",
    evaluationMethod: "No evaluation was completed.",
    configuration: ["Run stopped before model training; no validation or test metrics were generated."],
    resultSource: "results/reports/phase7-20261104T100155Z-seed2025/run.json",
    sourceReport: "Run metadata only; no experiment results.",
    limitations: ["Not an evaluated model. No score is available."],
  },
  {
    id: "phase7-xgboost-300",
    runId: "phase7-20261104T100506Z-seed2025",
    name: "XGBoost 300-round comparison",
    phase: "Phase 7",
    status: "complete",
    timestamp: "2026-11-04T12:18:32.379703Z",
    savedResults: true,
    classification: "measured_experimental_result",
    objective: "Evaluate a boosted tree model on the same behavioral correctness target.",
    hypothesis: "No formal hypothesis is recorded in the saved run report.",
    dataset: "EdNet KT1",
    split: "Unseen-learner validation; 14,236,525 examples; same deterministic 5% learner training sample as Phase 6.",
    target: "Submitted-answer correctness; behavioral outcome.",
    evaluationMethod: "Validation metrics and 15-bin calibration on the full validation cohort; early stopping used a validation subset. Test partition not used.",
    configuration: ["XGBoost histogram trees; maximum 300 estimators; best iteration 299.", "Learning rate 0.05; max depth 6; subsample/column sample 0.8; seed 2025."],
    resultSource: "results/reports/phase7-20261104T100506Z-seed2025/run.json; validation_metrics.csv; calibration_bins.csv",
    sourceReport: "docs/XGBOOST_EXPERIMENT.md; docs/ADVANCED_MODEL_COMPARISON.md",
    limitations: ["This is a sampled-training validation result, not a locked-test result.", "Tree feature importance is not causal evidence."],
  },
  {
    id: "phase7-random-forest",
    runId: "phase7-20261104T121919Z-seed2025",
    name: "Random Forest evaluation",
    phase: "Phase 7",
    status: "complete",
    timestamp: "2026-11-04T13:05:03.151279Z",
    savedResults: true,
    classification: "measured_experimental_result",
    objective: "Evaluate a Random Forest on the behavioral correctness target.",
    hypothesis: "No formal hypothesis is recorded in the saved run report.",
    dataset: "EdNet KT1",
    split: "Unseen-learner validation; 14,236,525 examples; same deterministic training learner sample as Phase 6/7.",
    target: "Submitted-answer correctness; behavioral outcome.",
    evaluationMethod: "Full validation metrics and 15 equal-width calibration bins. Test partition not used.",
    configuration: ["24 trees; maximum depth 12; minimum leaf size 500.", "Bootstrap sample fraction 0.5; max_features sqrt; seed 2025."],
    resultSource: "results/reports/phase7-20261104T121919Z-seed2025/run.json; validation_metrics.csv; calibration_bins.csv",
    sourceReport: "docs/RANDOM_FOREST_EXPERIMENT.md; docs/ADVANCED_MODEL_COMPARISON.md",
    limitations: ["Pooled validation metrics only; no learner-bootstrap interval.", "The high recall/F1 should be read alongside the model's near-all-positive predictions and weaker discrimination."],
  },
  {
    id: "phase7-xgboost-resumed",
    runId: "phase7-xgb-resume-20261105T040130Z-seed2025",
    name: "XGBoost continuation to 600 rounds",
    phase: "Phase 7",
    status: "complete",
    timestamp: "2026-11-05T06:05:33.145591Z",
    savedResults: true,
    classification: "measured_experimental_result",
    objective: "Continue the existing XGBoost checkpoint and evaluate the resulting behavioral correctness predictions.",
    hypothesis: "No formal hypothesis is recorded in the saved run report.",
    dataset: "EdNet KT1",
    split: "Unseen-learner validation; 14,236,525 examples; same 5% learner training sample.",
    target: "Submitted-answer correctness; behavioral outcome.",
    evaluationMethod: "Validation log loss for early stopping; full validation report and calibration bins. Test partition not used.",
    configuration: ["Resumed from 300 rounds; 300 additional rounds maximum; total 600; best iteration 599.", "Learning rate 0.05; max depth 6; early stopping 30 rounds; seed 2025."],
    resultSource: "results/reports/phase7-xgb-resume-20261105T040130Z-seed2025/run.json; validation_metrics.csv; calibration_bins.csv",
    sourceReport: "docs/XGBOOST_CONTINUATION_EXPERIMENT.md; docs/ADVANCED_MODEL_COMPARISON.md",
    limitations: ["Same sampled training protocol and validation partition as Phase 6/7; no test result.", "Model comparisons do not estimate cognitive understanding."],
  },
  {
    id: "phase8-sequence-failed",
    runId: "phase8-temporal-20261105T070210Z-seed2025",
    name: "Initial Phase 8 sequence-model attempt",
    phase: "Phase 8",
    status: "failed",
    timestamp: "2026-11-05T07:02:10.391253Z",
    savedResults: false,
    classification: "not_evaluated",
    objective: "Attempt sequence model training for next-response correctness.",
    hypothesis: "No saved hypothesis or evaluation result.",
    dataset: "EdNet KT1",
    split: "Unseen-learner training/validation role groups; run stopped before evaluation.",
    target: "Next submitted-answer correctness; behavioral outcome.",
    evaluationMethod: "No prediction evaluation was completed.",
    configuration: ["Run stopped after an attention-mask shape error; no metrics were produced."],
    resultSource: "results/reports/phase8-temporal-20261105T070210Z-seed2025/run.json",
    sourceReport: "No evaluation report; failure details are recorded in run.json.",
    limitations: ["Not an evaluated model. No score is available."],
  },
  {
    id: "phase8-sequence-report",
    runId: "phase8-temporal-20261105T073420Z-seed2025",
    name: "Matched DKT and SAKT-style comparison",
    phase: "Phase 8",
    status: "complete",
    timestamp: "2026-11-05T08:12:01.053641Z",
    savedResults: true,
    classification: "measured_experimental_result",
    objective: "Compare sequence-model and existing behavioral predictors on matched report-only next-response rows.",
    hypothesis: "No formal hypothesis is recorded in the saved experiment metadata.",
    dataset: "EdNet KT1",
    split: "Learner-disjoint validation; separate early-stop and calibration learner groups; 11,382,220 matched report-only transitions from 90,982 learners.",
    target: "Next submitted-answer correctness; behavioral outcome.",
    evaluationMethod: "Fixed 0.5 threshold; pooled metrics; 1,000-resample paired learner bootstrap for selected differences; report-only metrics not used to fit temperature.",
    configuration: ["DKT and SAKT use question identity and strictly prior response correctness; maximum sequence length 200.", "Training uses the same deterministic 5% unseen-learner sample; AdamW, learning rate 1e-3, weight decay 1e-5.", "Temperature scaling was fitted on a separate learner-disjoint calibration group."],
    resultSource: "results/reports/phase8-temporal-20261105T073420Z-seed2025/{experiment,validation_metrics,validation_calibration_bins,paired_learner_bootstrap_vs_logistic}.csv/json",
    sourceReport: "docs/PHASE8_SEQUENCE_MODEL_COMPARISON.md; docs/PHASE8_CALIBRATION_ANALYSIS.md; docs/TEMPORAL_KNOWLEDGE_TRACING_EXPERIMENT.md",
    limitations: ["Different model families use different input representations; this is not an architecture-only ablation.", "The report-only cohort is validation, not an independent test; bootstrap is conditional on a single trained run."],
  },
];

export const metricDefinitions: Record<MetricKey, { label: string; description: string; direction: "higher" | "lower" }> = {
  accuracy: { label: "Accuracy", description: "Share of responses classified correctly at the fixed 0.5 threshold.", direction: "higher" },
  precision: { label: "Precision", description: "Among responses predicted correct, share that were correct.", direction: "higher" },
  recall: { label: "Recall", description: "Among correct responses, share predicted correct.", direction: "higher" },
  f1: { label: "F1", description: "Harmonic mean of precision and recall for the correct-answer class.", direction: "higher" },
  rocAuc: { label: "ROC-AUC", description: "Discrimination across classification thresholds; does not measure probability calibration.", direction: "higher" },
  prAuc: { label: "PR-AUC / AP", description: "Average precision for the correct-answer class; prevalence affects interpretation.", direction: "higher" },
  logLoss: { label: "Log loss", description: "Penalizes probabilistic predictions, especially confident errors.", direction: "lower" },
  brierScore: { label: "Brier score", description: "Mean squared error of predicted probabilities for binary outcomes.", direction: "lower" },
  ece: { label: "ECE · 15 bins", description: "Equal-width expected calibration error; depends on binning and cohort prevalence.", direction: "lower" },
};

export const metricOrder: MetricKey[] = ["accuracy", "precision", "recall", "f1", "rocAuc", "prAuc", "logLoss", "brierScore", "ece"];

export const classificationLabels: Record<ResultClassification, string> = {
  measured_experimental_result: "Measured experimental result",
  engineering_validation: "Engineering validation",
  synthetic_evaluation: "Synthetic evaluation",
  unvalidated_hypothesis: "Unvalidated hypothesis",
  not_evaluated: "Not evaluated",
};

export function getCohort(cohortId: string): EvaluationCohort | undefined {
  return evaluationCohorts.find((cohort) => cohort.id === cohortId);
}

export function getModelResult(cohortId: string, modelId: string): ModelResult | undefined {
  const result = getCohort(cohortId)?.models.find((model) => model.modelId === modelId);
  return result ? { ...result, cohortId } : undefined;
}

export function getCohortModels(cohortId: string): ModelResult[] {
  return getCohort(cohortId)?.models.map((model) => ({ ...model, cohortId })) ?? [];
}

export function getMetrics(model: ModelResult, variant: CalibrationVariant = "raw"): Partial<Record<MetricKey, number | null>> {
  return model.metricVariants?.[variant] ?? model.metrics ?? {};
}

export function getCalibrationBins(model: ModelResult, variant: CalibrationVariant = "raw"): CalibrationBin[] {
  const bins = model.calibrationBins;
  if (!bins) return [];
  return Array.isArray(bins) ? bins : bins[variant] ?? [];
}

export function compareResults(results: ModelResult[]): { compatible: boolean; warning: string | null } {
  if (results.length < 2) return { compatible: true, warning: null };
  const cohortIds = new Set(results.map((result) => result.cohortId).filter(Boolean));
  if (cohortIds.size === 1 && results.every((result) => result.cohortId)) return { compatible: true, warning: null };
  const cohortKeys = new Set(results.map((result) => result.source));
  if (cohortKeys.size === 1) return { compatible: true, warning: null };
  const contextKeys = new Set(results.map((result) => `${result.metricsSource}|${result.examples}|${result.learners}|${result.resultClassification}`));
  return contextKeys.size === 1
    ? { compatible: true, warning: "These records share a reported cohort and sample size, but inspect their source reports for differences in training protocol or inputs." }
    : { compatible: false, warning: "These results come from different report sources or evaluation cohorts. Do not read them as a direct model comparison." };
}

export function formatMetric(value: number | null | undefined, key: MetricKey): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Unavailable";
  if (["accuracy", "precision", "recall", "f1", "rocAuc", "prAuc", "ece"].includes(key)) return `${(value * 100).toFixed(2)}%`;
  return value.toFixed(4);
}

export function getExperiment(experimentId: string): ExperimentRecord | undefined {
  return experiments.find((experiment) => experiment.id === experimentId);
}

export function getDashboardSummary() {
  const measuredRuns = experiments.filter((experiment) => experiment.savedResults && experiment.classification === "measured_experimental_result");
  const families = new Set(evaluationCohorts.flatMap((cohort) => cohort.models.map((model) => model.family)));
  const availableMetrics = new Set(evaluationCohorts.flatMap((cohort) => cohort.models.flatMap((model) => Object.keys(model.metrics ?? model.metricVariants?.raw ?? {}))));
  return {
    measuredRuns: measuredRuns.length,
    modelFamilies: families.size,
    datasets: new Set(evaluationCohorts.map((cohort) => cohort.dataset)).size,
    predictionMetricCount: availableMetrics.size,
    cohorts: evaluationCohorts.length,
    engineeringValidations: phaseValidations.length,
  };
}

export function inventoryForClassification(classification: ResultClassification): ArtifactInventoryItem[] {
  return artifactInventory.filter((item) => item.classification === classification);
}

export function evaluateArtifactState<T>(data: T[] | undefined, error?: string | null): "error" | "empty" | "ready" {
  if (error) return "error";
  if (!data || data.length === 0) return "empty";
  return "ready";
}

export function phaseMetric(phase: PhaseValidation, key: string): number | string | undefined {
  const value = phase[key];
  return typeof value === "number" || typeof value === "string" ? value : undefined;
}

