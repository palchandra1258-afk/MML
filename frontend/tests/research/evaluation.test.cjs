const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const test = require("node:test");
const {
  artifactInventory,
  compareResults,
  evaluateArtifactState,
  experiments,
  formatMetric,
  getCalibrationBins,
  getCohort,
  getCohortModels,
  getDashboardSummary,
  getExperiment,
  getMetrics,
  getModelResult,
  phaseValidations,
} = require("../../.api-test-dist/lib/research/catalog.js");

const full = "unseen-validation-full";
const sequence = "phase8-matched-report-only";

test("research artifact inventory includes result reports, checkpoints, failed runs and excluded learner-level files", () => {
  assert.ok(artifactInventory.length >= 20);
  assert.ok(artifactInventory.some((item) => item.path.includes("phase8-temporal-20261105T070210Z") && item.classification === "not_evaluated"));
  assert.ok(artifactInventory.some((item) => item.path.includes("validation_learner_states.jsonl") && !item.included));
  assert.ok(artifactInventory.some((item) => item.classification === "synthetic_evaluation"));
});

test("overview counts come from evaluated artifacts, excluding interrupted and failed attempts", () => {
  assert.deepEqual(getDashboardSummary(), { measuredRuns: 5, modelFamilies: 6, datasets: 1, predictionMetricCount: 9, cohorts: 2, engineeringValidations: 5 });
  assert.equal(experiments.filter((item) => item.savedResults).length, 5);
  assert.equal(experiments.filter((item) => !item.savedResults).length, 2);
});

test("experiment metadata contains objective, target, protocol, configuration, limitations and source references", () => {
  for (const experiment of experiments) {
    assert.ok(experiment.objective);
    assert.ok(experiment.hypothesis);
    assert.ok(experiment.dataset);
    assert.ok(experiment.split);
    assert.ok(experiment.target);
    assert.ok(experiment.evaluationMethod);
    assert.ok(experiment.resultSource);
    assert.ok(experiment.sourceReport);
    assert.ok(experiment.limitations.length > 0);
  }
  assert.equal(getExperiment("phase8-sequence-failed").savedResults, false);
  assert.equal(getExperiment("ednet-logistic-validation").runId, undefined);
  assert.equal(getExperiment("phase8-sequence-report").runId, "phase8-temporal-20261105T073420Z-seed2025");
});

test("model comparisons contain only evaluated model variants for the selected cohort", () => {
  assert.equal(getCohort(full).models.length, 7);
  assert.equal(getCohort(sequence).models.length, 8);
  assert.ok(getCohort(sequence).models.some((model) => model.modelId === "dkt"));
  assert.ok(getCohort(sequence).models.some((model) => model.modelId === "sakt"));
  assert.ok(getCohort(sequence).models.every((model) => model.confusionMatrix?.length === 2));
});

test("missing metric values remain unavailable and are not converted to zero", () => {
  assert.equal(formatMetric(undefined, "accuracy"), "Unavailable");
  assert.equal(formatMetric(null, "brierScore"), "Unavailable");
  assert.equal(formatMetric(Number.NaN, "ece"), "Unavailable");
});

test("each model metric has dataset, split, classification and artifact provenance", () => {
  const logistic = getModelResult(full, "sgd_logistic");
  assert.equal(logistic.resultClassification, "measured_experimental_result");
  assert.equal(logistic.metricsSource, "results/reports/phase7-xgb-resume-20261105T040130Z-seed2025/validation_metrics.csv");
  assert.equal(getCohort(full).dataset, "EdNet KT1");
  assert.match(getCohort(full).split, /Learner-disjoint validation/);
  assert.match(getCohort(full).protocol, /Locked test partition was not used/);
});

test("comparison helper distinguishes same-cohort comparisons from incompatible report cohorts", () => {
  assert.deepEqual(compareResults(getCohortModels(full)), { compatible: true, warning: null });
  const crossCohort = [getModelResult(full, "sgd_logistic"), getModelResult(sequence, "sgd_logistic")];
  assert.equal(compareResults(crossCohort).compatible, false);
  assert.match(compareResults(crossCohort).warning, /different report sources or evaluation cohorts/);
});

test("Phase 8 raw and temperature-scaled calibration metrics are sourced separately", () => {
  const sakt = getModelResult(sequence, "sakt");
  assert.notEqual(getMetrics(sakt, "raw").ece, getMetrics(sakt, "temperature_scaled").ece);
  assert.equal(sakt.calibrationMethod.includes("separate learner-disjoint calibration cohort"), true);
  assert.ok(sakt.temperature > 0);
});

test("reliability diagram data comes from occupied saved bins only", () => {
  const bins = getCalibrationBins(getModelResult(sequence, "majority"), "raw");
  assert.equal(bins.length, 15);
  assert.ok(bins.some((bin) => bin.count > 0 && bin.meanProbability !== null && bin.observedPositiveRate !== null));
  assert.ok(bins.some((bin) => bin.count === 0 && bin.meanProbability === null));
});

test("saved Phase 8 confusion matrices are surfaced with their actual artifact source", () => {
  const sakt = getModelResult(sequence, "sakt");
  assert.equal(sakt.confusionMatrix.length, 2);
  assert.match(sakt.confusionMatrixSource, /phase8-temporal-20261105T073420Z-seed2025\/experiment.json/);
});

test("missing reliability-bin data is represented as empty, not an invented curve", () => {
  assert.deepEqual(getCalibrationBins({ calibrationMethod: "", temperature: null }, "raw"), []);
  assert.equal(evaluateArtifactState([]), "empty");
});

test("behavioral-state summary distinguishes descriptive state construction from model prediction", () => {
  const phase9 = phaseValidations.find((phase) => phase.id.startsWith("phase9"));
  assert.equal(phase9.learners, 117785);
  assert.equal(phase9.interactions, 14241124);
  assert.equal(phase9.modelPredictionAvailable, 0);
  assert.equal(phase9.confidenceIntervals, "Not reported");
  assert.equal(phase9.historicalAccuracyMacroMean, 0.49181536054721464);
  assert.equal(phase9.recentAccuracyMacroMean, 0.49670491801512023);
  assert.equal(phase9.directCognitiveAccuracy, null);
});

test("cognitive-state summary explicitly disclaims ground-truth accuracy", () => {
  const phase11 = phaseValidations.find((phase) => phase.id.startsWith("phase11"));
  assert.equal(phase11.snapshots, 184);
  assert.equal(phase11.learners, 100);
  assert.match(phase11.groundTruth, /No validated cognitive-state labels/);
  assert.match(phase11.samplingLimit, /not random or population estimate/);
  assert.match(phase11.evidenceReferenceValidation, /all 184 snapshots/);
  assert.match(phase11.realLearnerModalityCoverage, /text\/audio\/visual media are absent/);
});

test("representation evaluation distinguishes traceability from capability and learning effectiveness", () => {
  const phase12 = phaseValidations.find((phase) => phase.id.startsWith("phase12"));
  assert.equal(phase12.plansBuilt, 1910);
  assert.equal(phase12.selectedRepresentations, 0);
  assert.equal(phase12.plansWithoutSelection, 1910);
  assert.equal(phase12.traceabilityRate, 1);
  assert.equal(phase12.learningEffectivenessEvaluated, false);
  assert.ok(Object.values(phase12.capabilityStatuses).every((value) => value === "unavailable"));
});

test("trajectory result preserves the zero-diversion denominator and bounded interpretation", () => {
  const phase13 = phaseValidations.find((phase) => phase.id.startsWith("phase13"));
  assert.equal(phase13.trajectories, 100);
  assert.equal(phase13.validTransitions, 100);
  assert.equal(phase13.invalidEdgesRejected, 44);
  assert.equal(phase13.diversions, 0);
  assert.match(phase13.diversionLimit, /registry was empty/);
  assert.equal(phase13.learningEffectivenessEvaluated, false);
});

test("measured, engineering, synthetic and not-evaluated classifications remain distinct", () => {
  assert.ok(getCohort(full).models.every((model) => model.resultClassification === "measured_experimental_result"));
  assert.ok(phaseValidations.every((phase) => phase.classification === "engineering_validation"));
  assert.ok(artifactInventory.some((item) => item.classification === "synthetic_evaluation"));
  assert.ok(experiments.some((item) => item.classification === "not_evaluated"));
});

test("experiment selection exposes allowlisted source report references without filesystem URLs", () => {
  const experiment = getExperiment("phase8-sequence-report");
  assert.match(experiment.resultSource, /results\/reports\/phase8-temporal/);
  assert.match(experiment.sourceReport, /docs\/PHASE8_SEQUENCE_MODEL_COMPARISON.md/);
  assert.ok(artifactInventory.some((item) => item.path.includes("phase8-temporal-20261105T073420Z")));
  assert.ok(!experiment.resultSource.startsWith("file://"));
});

test("empty and artifact error states are distinct", () => {
  assert.equal(evaluateArtifactState(undefined), "empty");
  assert.equal(evaluateArtifactState([]), "empty");
  assert.equal(evaluateArtifactState([], "snapshot unavailable"), "error");
  assert.equal(evaluateArtifactState([{}]), "ready");
});

test("research navigation and tables have responsive and keyboard-scroll affordances", () => {
  const component = readFileSync(resolve(__dirname, "../../components/research/research-evaluation-page.tsx"), "utf8");
  const css = readFileSync(resolve(__dirname, "../../app/globals.css"), "utf8");
  assert.match(component, /aria-label="Research evaluation sections"/);
  assert.match(component, /role="region" aria-label="Model comparison table" tabIndex=\{0\}/);
  assert.match(css, /\.research-section-nav/);
  assert.match(css, /@media \(max-width: 600px\)/);
  assert.match(css, /\.research-table-scroll:focus-visible/);
});

