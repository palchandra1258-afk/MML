"use client";

import { useState } from "react";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/data-states";
import {
  artifactInventory,
  classificationLabels,
  compareResults,
  evaluateArtifactState,
  evaluationCohorts,
  experiments,
  formatMetric,
  getCalibrationBins,
  getCohort,
  getCohortModels,
  getDashboardSummary,
  getExperiment,
  getMetrics,
  getModelResult,
  metricDefinitions,
  metricOrder,
  missingArtifacts,
  phaseValidations,
  snapshotDate,
  snapshotType,
  type CalibrationVariant,
  type MetricKey,
  type ModelResult,
  type PhaseValidation,
  type ResultClassification,
} from "@/lib/research/catalog";

const summary = getDashboardSummary();
const metricColumns: MetricKey[] = ["accuracy", "precision", "recall", "f1", "rocAuc", "prAuc", "logLoss", "brierScore", "ece"];

export function ResearchEvaluationPage() {
  const initialCohort = evaluationCohorts[0];
  const [cohortId, setCohortId] = useState(initialCohort?.id ?? "");
  const [selectedModels, setSelectedModels] = useState<string[]>(initialCohort?.models.map((model) => model.modelId) ?? []);
  const [focusModelId, setFocusModelId] = useState(initialCohort?.models[0]?.modelId ?? "");
  const [comparisonVariant, setComparisonVariant] = useState<CalibrationVariant>("raw");
  const [calibrationCohortId, setCalibrationCohortId] = useState(evaluationCohorts[1]?.id ?? initialCohort?.id ?? "");
  const [calibrationModelId, setCalibrationModelId] = useState(evaluationCohorts[1]?.models[3]?.modelId ?? initialCohort?.models[0]?.modelId ?? "");
  const [calibrationVariant, setCalibrationVariant] = useState<CalibrationVariant>("raw");
  const [experimentId, setExperimentId] = useState(experiments.find((item) => item.savedResults)?.id ?? "");

  const cohort = getCohort(cohortId);
  const models = cohort?.models ?? [];
  const selectedResults = getCohortModels(cohortId).filter((model) => selectedModels.includes(model.modelId));
  const compatibility = compareResults(selectedResults);
  const focusModel = getModelResult(cohortId, focusModelId);
  const selectedExperiment = getExperiment(experimentId);
  const calibrationCohort = getCohort(calibrationCohortId);
  const calibrationModels = calibrationCohort?.models ?? [];
  const calibrationModel = getModelResult(calibrationCohortId, calibrationModelId);
  const calibrationBins = calibrationModel ? getCalibrationBins(calibrationModel, calibrationVariant) : [];
  const calibrationMetrics = calibrationModel ? getMetrics(calibrationModel, calibrationVariant) : {};
  const availableCalibrationVariants = calibrationModel?.metricVariants ? ["raw", "temperature_scaled"] as CalibrationVariant[] : ["raw"] as CalibrationVariant[];

  function changeCohort(nextId: string) {
    const nextCohort = getCohort(nextId);
    setCohortId(nextId);
    setSelectedModels(nextCohort?.models.map((model) => model.modelId) ?? []);
    setFocusModelId(nextCohort?.models[0]?.modelId ?? "");
    setComparisonVariant("raw");
  }

  function changeCalibrationCohort(nextId: string) {
    const nextCohort = getCohort(nextId);
    setCalibrationCohortId(nextId);
    setCalibrationModelId(nextCohort?.models[3]?.modelId ?? nextCohort?.models[0]?.modelId ?? "");
    setCalibrationVariant("raw");
  }

  function toggleModel(modelId: string) {
    setSelectedModels((current) => current.includes(modelId) ? current.filter((id) => id !== modelId) : [...current, modelId]);
    setFocusModelId(modelId);
  }

  function viewExperimentResults(selectedId: string) {
    const targets: Record<string, [string, string]> = {
      "ednet-logistic-validation": ["unseen-validation-full", "sgd_logistic"],
      "phase7-xgboost-300": ["unseen-validation-full", "xgboost_300_round"],
      "phase7-random-forest": ["unseen-validation-full", "random_forest"],
      "phase7-xgboost-resumed": ["unseen-validation-full", "xgboost_resumed"],
      "phase8-sequence-report": ["phase8-matched-report-only", "dkt"],
    };
    const target = targets[selectedId];
    if (!target || !getModelResult(target[0], target[1])) return;
    setCohortId(target[0]);
    setSelectedModels([target[1]]);
    setFocusModelId(target[1]);
    setComparisonVariant("raw");
    document.getElementById("model-comparison")?.scrollIntoView();
  }

  return <div className="research-evaluation-page">
    <header className="research-evaluation-hero">
      <div className="research-breadcrumb"><span>Research console</span><span aria-hidden="true">/</span><span>Model evaluation</span></div>
      <div className="research-title-row">
        <div><p className="eyebrow">F6 · RESEARCH AND EVALUATION</p><h1>Evidence behind the results</h1><p className="section-detail">Inspect measured behavior prediction results alongside the engineering checks and research questions that remain open.</p></div>
        <StatusBadge tone="purple" dot>Versioned report snapshot · {snapshotDate}</StatusBadge>
      </div>
      <nav className="research-section-nav" aria-label="Research evaluation sections">
        <a href="#overview">Overview</a><a href="#model-comparison">Model comparison</a><a href="#performance">Performance</a><a href="#calibration">Calibration</a><a href="#system-validation">Phase 9–13 validation</a><a href="#experiment-inventory">Run inventory</a>
      </nav>
    </header>

    <aside className="research-snapshot-notice" aria-label="Research artifact source">
      <span className="research-notice-mark" aria-hidden="true">i</span>
      <p><strong>Artifact source.</strong> {snapshotType} The OpenAPI contract has no evaluation-report endpoint. No repository files are read by the browser, and API health is not treated as an evaluation feed.</p>
    </aside>

    <section id="overview" className="research-section">
      <SectionHeading eyebrow="RESEARCH OVERVIEW" title="What has saved evidence" detail="Counts below are derived from the inspected aggregate report inventory. A run, a model family and an engineering check are counted separately."/>
      <div className="research-summary-grid">
        <SummaryMetric value={summary.measuredRuns} label="Predictive runs with saved metrics" source="Phase 6–8 result reports; interrupted or failed runs excluded."/>
        <SummaryMetric value={summary.modelFamilies} label="Model families evaluated" source="Baseline, logistic, Random Forest, XGBoost, DKT and SAKT-style."/>
        <SummaryMetric value={summary.datasets} label="Prediction datasets" source="EdNet KT1; one behavioral response target."/>
        <SummaryMetric value={summary.predictionMetricCount} label="Scalar prediction metrics" source="Only metrics present in saved validation reports are included."/>
      </div>
      <div className="research-claim-strip">
        <div><StatusBadge tone="teal">Measured</StatusBadge><p>Unseen-learner validation supports comparison of next-answer correctness predictors.</p></div>
        <div><StatusBadge tone="amber">Not established</StatusBadge><p>No locked-test result, cognitive ground truth, representation outcome or learning-gain study is reported.</p></div>
        <div><StatusBadge tone="purple">Separate evidence</StatusBadge><p>Phases 9–13 report state construction, traceability and orchestration checks, not cognitive accuracy.</p></div>
      </div>
    </section>

    <section id="model-comparison" className="research-section">
      <SectionHeading eyebrow="MODEL COMPARISON" title="Compare within a declared cohort" detail="Select an evaluation cohort first. The dashboard does not rank all models across different report protocols."/>
      {evaluationCohorts.length === 0 ? <EmptyState title="No model evaluation cohorts are available">No aggregate model evaluation records are included in this snapshot.</EmptyState> : <>
        <div className="research-control-row">
          <label className="research-control"><span>Evaluation cohort</span><select value={cohortId} onChange={(event) => changeCohort(event.target.value)}>{evaluationCohorts.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
          {models.some((model) => model.metricVariants) && <label className="research-control"><span>Probability report</span><select value={comparisonVariant} onChange={(event) => setComparisonVariant(event.target.value as CalibrationVariant)}><option value="raw">Raw predictions</option><option value="temperature_scaled">Temperature scaled</option></select></label>}
          <div className="research-cohort-meta"><strong>{cohort?.dataset ?? "Dataset unavailable"}</strong><span>{cohort?.examples.toLocaleString() ?? "—"} examples · {cohort?.learners.toLocaleString() ?? "—"} learners</span><span>{cohort?.classification && <ClassificationBadge classification={cohort.classification}/>}</span></div>
        </div>
        {cohort && <div className="research-protocol-panel"><strong>Target and protocol</strong><p>{cohort.target}</p><p>{cohort.split} {cohort.protocol}</p><SourceLine label="Metrics source" source={cohort.metricsSource}/></div>}
        <div className="research-model-selector" aria-label="Select models to compare">
          {models.map((model) => <label key={model.modelId} className="research-model-choice"><input type="checkbox" checked={selectedModels.includes(model.modelId)} onChange={() => toggleModel(model.modelId)}/><span><strong>{model.label}</strong><small>{model.variant}</small></span></label>)}
        </div>
        {!selectedResults.length ? <EmptyState title="Select at least one model">Choose one or more evaluated models to inspect their saved metrics.</EmptyState> : <>
          {!compatibility.compatible && compatibility.warning && <div className="research-warning" role="alert">{compatibility.warning}</div>}
          {compatibility.compatible && compatibility.warning && <div className="research-info" role="note">{compatibility.warning}</div>}
          <div className="research-table-scroll" role="region" aria-label="Model comparison table" tabIndex={0}>
            <table className="research-table research-comparison-table"><thead><tr><th scope="col">Model</th>{metricColumns.map((key) => <th scope="col" key={key} title={metricDefinitions[key].description}>{metricDefinitions[key].label}</th>)}<th scope="col">Result evidence</th></tr></thead>
              <tbody>{selectedResults.map((model) => { const values = getMetrics(model, comparisonVariant); return <tr key={model.modelId} className={focusModelId === model.modelId ? "research-row-focused" : ""}>
                <th scope="row"><button className="research-model-link" type="button" onClick={() => setFocusModelId(model.modelId)}>{model.label}</button><small>{model.variant}</small></th>
                {metricColumns.map((key) => <td key={key} title={metricDefinitions[key].description}>{formatMetric(values[key], key)}</td>)}
                <td className="research-source-cell"><ClassificationBadge classification={model.resultClassification}/><code>{model.metricsSource}</code><small>{model.runId} · {model.evaluatedAt ? new Date(model.evaluatedAt).toLocaleString() : "timestamp unavailable"}</small></td>
              </tr>; })}</tbody>
            </table>
          </div>
          <p className="research-table-note">Missing metric values remain unavailable. The table has no aggregate score or universal rank. Lower log loss, Brier score and ECE are generally preferable; interpretation still depends on the cohort and protocol.</p>
        </>}
      </>}
    </section>

    <section id="performance" className="research-section">
      <SectionHeading eyebrow="PREDICTION PERFORMANCE" title="Metric definitions and saved outputs" detail="Discrimination, thresholded classification and probability quality answer different questions. These scores concern response correctness only."/>
      {!focusModel ? <EmptyState title="No model selected for inspection">Choose an evaluated model in the comparison section.</EmptyState> : <>
        <div className="research-detail-controls"><label className="research-control"><span>Model record</span><select value={focusModelId} onChange={(event) => setFocusModelId(event.target.value)}>{models.map((model) => <option value={model.modelId} key={model.modelId}>{model.label}</option>)}</select></label><ClassificationBadge classification={focusModel.resultClassification}/></div>
        <div className="research-metric-grid">{metricOrder.map((key) => {
          const value = getMetrics(focusModel, comparisonVariant)[key];
          return <article key={key} className="research-metric-card"><span>{metricDefinitions[key].label}</span><strong>{formatMetric(value, key)}</strong><p>{metricDefinitions[key].description}</p><small>{value === null || value === undefined ? "Not present in this result artifact" : `Source: ${focusModel.metricsSource}`}</small></article>;
        })}</div>
        <div className="research-provenance-grid">
          <div className="research-protocol-panel"><strong>Provenance</strong><dl><dt>Dataset</dt><dd>{cohort?.dataset}</dd><dt>Split and cohort</dt><dd>{cohort?.split}</dd><dt>Evaluation method</dt><dd>{cohort?.protocol}</dd><dt>Metric source</dt><dd><code>{focusModel.metricsSource}</code></dd><dt>Calibration bins</dt><dd><code>{focusModel.calibrationSource}</code></dd><dt>Classification</dt><dd><ClassificationBadge classification={focusModel.resultClassification}/></dd></dl></div>
          <ConfusionMatrix model={focusModel}/>
        </div>
      </>}
    </section>

    <section id="calibration" className="research-section">
      <SectionHeading eyebrow="PROBABILITY CALIBRATION" title="Observed frequency versus predicted probability" detail="Discrimination asks whether scores separate outcomes. Calibration asks whether predicted probabilities match observed frequencies."/>
      <div className="research-control-row research-calibration-controls">
        <label className="research-control"><span>Calibration cohort</span><select value={calibrationCohortId} onChange={(event) => changeCalibrationCohort(event.target.value)}>{evaluationCohorts.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}</select></label>
        <label className="research-control"><span>Model</span><select value={calibrationModelId} onChange={(event) => setCalibrationModelId(event.target.value)}>{calibrationModels.map((model) => <option value={model.modelId} key={model.modelId}>{model.label}</option>)}</select></label>
        <label className="research-control"><span>Probability series</span><select value={calibrationVariant} onChange={(event) => setCalibrationVariant(event.target.value as CalibrationVariant)}>{availableCalibrationVariants.map((variant) => <option key={variant} value={variant}>{variant === "raw" ? "Raw probabilities" : "Temperature scaled"}</option>)}</select></label>
      </div>
      {!calibrationModel ? <EmptyState title="Calibration record unavailable">There is no saved calibration record for this selection.</EmptyState> : <div className="research-calibration-layout">
        <article className="research-panel research-reliability-panel"><div className="research-panel-heading"><div><h3>Reliability diagram</h3><p>Only occupied bins with saved mean probability and observed rate are plotted.</p></div><ClassificationBadge classification={calibrationModel.resultClassification}/></div>
          <ReliabilityDiagram model={calibrationModel} bins={calibrationBins}/>
          <div className="research-chart-legend"><span><i className="research-legend-observed"/>Observed positive rate</span><span><i className="research-legend-ideal"/>Perfect calibration reference</span></div>
          <SourceLine label="Calibration bins" source={calibrationModel.calibrationSource}/>
        </article>
        <article className="research-panel research-calibration-summary"><div className="research-panel-heading"><div><h3>{calibrationModel.label}</h3><p>{calibrationCohort?.label}</p></div></div>
          <div className="research-calibration-values"><MetricValue label="Brier score" value={formatMetric(calibrationMetrics.brierScore, "brierScore")}/><MetricValue label="ECE · 15 bins" value={formatMetric(calibrationMetrics.ece, "ece")}/><MetricValue label="Log loss" value={formatMetric(calibrationMetrics.logLoss, "logLoss")}/><MetricValue label="Temperature" value={calibrationVariant === "temperature_scaled" && calibrationModel.temperature !== null ? calibrationModel.temperature.toFixed(4) : "Not applied"}/></div>
          <p className="research-method-note">{calibrationModel.calibrationMethod}. A low ECE alone does not demonstrate useful individual ranking, and post-hoc scaling may improve one metric while worsening another.</p>
          {calibrationVariant === "temperature_scaled" && <p className="research-info" role="note">Classification and ranking scores are unchanged by temperature scaling in this report; only probability metrics are interpreted as recalibrated.</p>}
        </article>
      </div>}
    </section>

    <section id="system-validation" className="research-section">
      <SectionHeading eyebrow="SYSTEM EVALUATION COVERAGE" title="What Phases 9–13 validated" detail="These reports assess state construction, schema/traceability, plan rules and orchestration. They do not establish cognition, representation effectiveness or learner benefit."/>
      <div className="research-validation-grid">{phaseValidations.map((phase) => <PhaseValidationCard key={phase.id} phase={phase}/>)}</div>
    </section>

    <section id="experiment-inventory" className="research-section">
      <SectionHeading eyebrow="REPRODUCIBILITY" title="Experiment and artifact inventory" detail="Select a run to inspect its saved objective, metadata, protocol, result classification and source references. File references are repository-relative labels; the browser does not open arbitrary server paths."/>
      <div className="research-table-scroll" role="region" aria-label="Research experiment inventory" tabIndex={0}>
        <table className="research-table research-inventory-table"><thead><tr><th scope="col">Phase</th><th scope="col">Run</th><th scope="col">Run status</th><th scope="col">Saved result</th><th scope="col">Source report</th></tr></thead><tbody>
          {experiments.map((experiment) => <tr key={experiment.id} className={experiment.id === experimentId ? "research-row-focused" : ""}>
            <td>{experiment.phase}</td><th scope="row"><button className="research-model-link" type="button" onClick={() => setExperimentId(experiment.id)}>{experiment.name}</button></th>
            <td><StatusBadge tone={experiment.status === "complete" ? "teal" : "amber"}>{experiment.status}</StatusBadge></td>
            <td><ClassificationBadge classification={experiment.classification}/></td>
            <td><code>{experiment.sourceReport}</code></td>
          </tr>)}
        </tbody></table>
      </div>
      {selectedExperiment && <ExperimentDetail experiment={selectedExperiment} onViewResults={() => viewExperimentResults(selectedExperiment.id)}/>}

      <div className="research-artifact-inventory">
        <h3>Audited artifact sources</h3>
        <div className="research-artifact-grid">{artifactInventory.map((item) => <article className="research-artifact-item" key={item.path}>
          <div><ClassificationBadge classification={item.classification}/><StatusBadge tone={item.included ? "teal" : "neutral"}>{item.included ? "Inspected" : "Excluded from dashboard counts"}</StatusBadge></div>
          <strong>{item.type}</strong><code>{item.path}</code>
        </article>)}</div>
      </div>
      <div className="research-missing-artifacts"><h3>Missing evidence and dependencies</h3><ul>{missingArtifacts.map((item) => <li key={item}>{item}</li>)}</ul></div>
    </section>

    <footer className="research-integrity-footer"><strong>Scientific interpretation boundary</strong><p>Correctness prediction is not cognitive understanding. Schema validation is not cognitive accuracy. Representation planning is not delivery or learning gain. Synthetic tests are not real learner evaluations. No locked test partition was opened or reused for this dashboard.</p></footer>
  </div>;
}

function SummaryMetric({ value, label, source }: { value: number; label: string; source: string }) {
  return <article className="research-summary-card"><strong>{value}</strong><span>{label}</span><small>{source}</small></article>;
}

function ClassificationBadge({ classification }: { classification: ResultClassification }) {
  const tone = classification === "measured_experimental_result" ? "teal" : classification === "engineering_validation" ? "purple" : classification === "synthetic_evaluation" ? "amber" : "neutral";
  return <StatusBadge tone={tone}>{classificationLabels[classification]}</StatusBadge>;
}

function SourceLine({ label, source }: { label: string; source: string }) {
  return <p className="research-source-line"><span>{label}</span><code>{source}</code></p>;
}

function MetricValue({ label, value }: { label: string; value: string }) {
  return <div className="research-calibration-value"><span>{label}</span><strong>{value}</strong></div>;
}

function ConfusionMatrix({ model }: { model: ModelResult }) {
  if (!model.confusionMatrix) return <div className="research-protocol-panel research-confusion-empty"><strong>Confusion matrix</strong><p>Unavailable in this selected evaluation record. No matrix was reconstructed from incomplete data.</p></div>;
  const [[tn, fp], [fn, tp]] = model.confusionMatrix;
  return <div className="research-protocol-panel"><strong>Saved confusion matrix</strong><p>True rows × predicted columns · labels: incorrect (0), correct (1)</p><table className="research-small-matrix"><thead><tr><th/><th scope="col">Predicted incorrect</th><th scope="col">Predicted correct</th></tr></thead><tbody><tr><th scope="row">Actually incorrect</th><td>{tn.toLocaleString()}</td><td>{fp.toLocaleString()}</td></tr><tr><th scope="row">Actually correct</th><td>{fn.toLocaleString()}</td><td>{tp.toLocaleString()}</td></tr></tbody></table><SourceLine label="Source" source={model.confusionMatrixSource ?? model.source}/></div>;
}

function ReliabilityDiagram({ model, bins }: { model: ModelResult; bins: ReturnType<typeof getCalibrationBins> }) {
  const points = bins.filter((bin) => bin.count > 0 && bin.meanProbability !== null && bin.observedPositiveRate !== null);
  if (evaluateArtifactState(points) !== "ready") return <div className="research-chart-empty"><strong>Reliability data unavailable</strong><p>No occupied calibration bins with both mean probability and observed frequency were saved for this selection.</p></div>;
  const x = (value: number) => 58 + Math.max(0, Math.min(1, value)) * 450;
  const y = (value: number) => 270 - Math.max(0, Math.min(1, value)) * 220;
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"}${x(point.meanProbability as number).toFixed(1)},${y(point.observedPositiveRate as number).toFixed(1)}`).join(" ");
  return <div className="research-chart-wrap">
    <svg className="research-reliability-chart" viewBox="0 0 560 330" role="img" aria-labelledby="reliability-title reliability-description">
      <title id="reliability-title">{`Reliability diagram for ${model.label}`}</title><desc id="reliability-description">Saved occupied probability bins. The horizontal axis is mean predicted probability and the vertical axis is observed frequency of a correct answer. The dashed diagonal is the perfect calibration reference.</desc>
      {[0, 0.5, 1].map((tick) => <g key={tick}><line x1="58" x2="508" y1={y(tick)} y2={y(tick)} className="research-chart-gridline"/><line x1={x(tick)} x2={x(tick)} y1="50" y2="270" className="research-chart-gridline"/><text x="46" y={y(tick) + 4} textAnchor="end">{tick.toFixed(1)}</text><text x={x(tick)} y="290" textAnchor="middle">{tick.toFixed(1)}</text></g>)}
      <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} className="research-chart-ideal"/>
      <path d={path} className="research-chart-observed"/>
      {points.map((point, index) => <circle key={`${point.lower}-${index}`} cx={x(point.meanProbability as number)} cy={y(point.observedPositiveRate as number)} r="4.5" className="research-chart-point"><title>{`Bin ${point.lower?.toFixed(2)}–${point.upper?.toFixed(2)}; n=${point.count.toLocaleString()}; mean probability=${point.meanProbability?.toFixed(4)}; observed frequency=${point.observedPositiveRate?.toFixed(4)}`}</title></circle>)}
      <text x="283" y="322" textAnchor="middle" className="research-chart-axis-label">Mean predicted probability</text><text transform="translate(15 160) rotate(-90)" textAnchor="middle" className="research-chart-axis-label">Observed positive frequency</text>
    </svg>
    <details className="research-calibration-data"><summary>Inspect saved calibration bins</summary><div className="research-table-scroll" role="region" aria-label="Calibration bin data" tabIndex={0}><table className="research-table"><thead><tr><th scope="col">Probability interval</th><th scope="col">Examples</th><th scope="col">Mean predicted</th><th scope="col">Observed frequency</th></tr></thead><tbody>{bins.map((bin, index) => <tr key={`${bin.lower}-${index}`}><th scope="row">{bin.lower === null || bin.upper === null ? "Unavailable" : `${bin.lower.toFixed(2)}–${bin.upper.toFixed(2)}`}</th><td>{bin.count.toLocaleString()}</td><td>{bin.meanProbability === null ? "Unavailable" : bin.meanProbability.toFixed(4)}</td><td>{bin.observedPositiveRate === null ? "Unavailable" : bin.observedPositiveRate.toFixed(4)}</td></tr>)}</tbody></table></div></details>
  </div>;
}

function ExperimentDetail({ experiment, onViewResults }: { experiment: NonNullable<ReturnType<typeof getExperiment>>; onViewResults: () => void }) {
  return <article id="experiment-details" className="research-panel research-experiment-detail">
    <div className="research-panel-heading"><div><p className="eyebrow">RUN DETAIL · {experiment.phase}</p><h3>{experiment.name}</h3><p>Run ID: <code>{experiment.runId ?? "Not recorded in the source artifact"}</code></p></div><div className="research-panel-actions"><ClassificationBadge classification={experiment.classification}/>{experiment.savedResults && <button className="research-action-button" type="button" onClick={onViewResults}>View saved metrics</button>}</div></div>
    <div className="research-experiment-grid"><div><strong>Research objective</strong><p>{experiment.objective}</p></div><div><strong>Hypothesis</strong><p>{experiment.hypothesis}</p></div><div><strong>Dataset and split</strong><p>{experiment.dataset} · {experiment.split}</p></div><div><strong>Target and method</strong><p>{experiment.target} {experiment.evaluationMethod}</p></div><div><strong>Run timestamp</strong><p>{experiment.timestamp ? new Date(experiment.timestamp).toLocaleString() : "Not recorded in the selected run metadata."}</p></div></div>
    <div className="research-experiment-grid"><div><strong>Saved configuration</strong><ul>{experiment.configuration.map((item) => <li key={item}>{item}</li>)}</ul></div><div><strong>Limitations</strong><ul>{experiment.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
    <div className="research-source-pair"><SourceLine label="Result artifacts" source={experiment.resultSource}/><SourceLine label="Source report" source={experiment.sourceReport}/></div>
    {!experiment.savedResults && <p className="research-warning" role="note">This run has no evaluation metrics. Its configuration or failure metadata is shown for audit completeness only.</p>}
  </article>;
}

function PhaseValidationCard({ phase }: { phase: PhaseValidation }) {
  const phaseNumber = phase.id.match(/^phase(\d+)/)?.[1].padStart(2, "0") ?? "??";
  const title = phaseNumber === "09" ? "Behavioral learner state" : phaseNumber === "10" ? "Evidence and provenance" : phaseNumber === "11" ? "Cognitive-state coverage" : phaseNumber === "12" ? "Representation planning" : "Trajectory orchestration";
  const facts: { label: string; value: string }[] = phaseNumber === "09" ? [
    { label: "Learners / snapshots", value: countText(phase.learners) }, { label: "Interactions · labeled", value: `${countText(phase.interactions)} · ${countText(phase.labelledResponses)}` }, { label: "Schema validated", value: countText(phase.schemaValidated) }, { label: "Model predictions", value: countText(phase.modelPredictionAvailable) }, { label: "Evidence sufficiency", value: objectSummary(phase.learnerEvidenceSufficiency) }, { label: "Observed historical correctness macro mean", value: percentText(phase.historicalAccuracyMacroMean) }, { label: "Observed recent correctness macro mean", value: percentText(phase.recentAccuracyMacroMean) }, { label: "Smoothed performance macro mean", value: percentText(phase.smoothedPerformanceMacroMean) }, { label: "Recent vs historical mean absolute difference", value: decimalText(phase.recentHistoricalMeanAbsoluteDifference) },
  ] : phaseNumber === "10" ? [
    { label: "Evidence records / learners", value: `${countText(phase.records)} / ${countText(phase.learners)}` }, { label: "Schema / provenance checks", value: `${countText(phase.schemaValidated)} / ${countText(phase.provenanceChecksPassed)}` }, { label: "Groups", value: countText(phase.groups) }, { label: "Alignment candidates", value: countText(phase.alignmentCandidates) },
  ] : phaseNumber === "11" ? [
    { label: "Snapshots / selected learners", value: `${countText(phase.snapshots)} / ${countText(phase.learners)}` }, { label: "Normalized interactions", value: countText(phase.normalizedInteractions) }, { label: "Rule hypothesis categories", value: objectSummary(phase.hypothesisCounts) }, { label: "Uncertainty", value: objectSummary(phase.uncertainty) }, { label: "Available real-data modality state", value: objectSummary(phase.availableModalityStates) }, { label: "Diagnostic recommendations", value: String(phase.diagnosticRecommendations ?? "Unavailable") },
  ] : phaseNumber === "12" ? [
    { label: "Plans built", value: countText(phase.plansBuilt) }, { label: "Selected representation", value: countText(phase.selectedRepresentations) }, { label: "Plans without selection", value: countText(phase.plansWithoutSelection) }, { label: "Capability availability", value: objectSummary(phase.capabilityStatuses) }, { label: "Plan actions", value: objectSummary(phase.actions) }, { label: "Alternative records", value: countText(phase.alternativeRecords) }, { label: "Reference matches", value: `${countText(phase.cognitiveStateReferenceMatches)} cognitive · ${countText(phase.evidenceReferenceMatches)} evidence` }, { label: "Temporal context preserved", value: `${countText(phase.temporalLinksWithContext)} / ${countText(phase.temporalLinks)} links` },
  ] : [
    { label: "Trajectories / transitions", value: `${countText(phase.trajectories)} / ${countText(phase.transitions)}` }, { label: "Valid transitions", value: `${countText(phase.validTransitions)} / ${countText(phase.transitions)}` }, { label: "Illegal edges rejected", value: `${countText(phase.invalidEdgesRejected)} / ${countText(phase.invalidEdgesTested)}` }, { label: "History events reconstructed", value: `${countText(phase.historyEventsReconstructed)} / ${countText(phase.historyEvents)}` }, { label: "Trajectory versions reconstructed", value: countText(phase.trajectoryVersionsReconstructed) }, { label: "Decision replay / evidence references", value: `${countText(phase.decisionReplayMatches)} / ${countText(phase.decisionReplayChecks)} · ${countText(phase.evidenceReferenceMatches)} / ${countText(phase.evidenceReferenceChecks)}` }, { label: "Diversions / resumptions", value: `${countText(phase.diversions)} / ${countText(phase.resumptions)}` },
  ];
  return <article className="research-panel research-validation-card"><div className="research-panel-heading"><div><p className="eyebrow">PHASE {phaseNumber}</p><h3>{title}</h3></div><ClassificationBadge classification={phase.classification}/></div>
    <div className="research-validation-facts">{facts.map((fact) => <div key={fact.label}><span>{fact.label}</span><strong>{fact.value}</strong></div>)}</div>
    {phaseNumber === "09" && <p className="research-method-note">Descriptive response summaries only. Confidence intervals are not reported; cognitive accuracy and predictive calibration are unavailable.</p>}
    {phaseNumber === "11" && <p className="research-warning" role="note">No validated cognitive-state ground truth. These are provisional rule categories; cognitive accuracy, misconception detection and diagnostic effectiveness are not established.</p>}
    {phaseNumber === "11" && <p className="research-method-note">{String(phase.evidenceReferenceValidation ?? "Evidence-reference validation detail was not reported.")}</p>}
    {phaseNumber === "11" && <p className="research-method-note">{String(phase.realLearnerModalityCoverage ?? "Real learner modality coverage is not reported.")}</p>}
    {phaseNumber === "12" && <p className="research-method-note">All eight capabilities were unavailable. Planning/traceability checks do not show representation delivery or learning effectiveness.</p>}
    {phaseNumber === "13" && <p className="research-method-note">{String(phase.diversionLimit ?? "Diversion outcomes unavailable.")}</p>}
    <SourceLine label="Aggregate source" source={phase.source}/><p className="research-report-source">Report: <code>{phase.report}</code></p>
  </article>;
}

function countText(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString() : "Unavailable";
}

function decimalText(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(4) : "Unavailable";
}

function percentText(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "Unavailable";
}

function objectSummary(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "Unavailable";
  return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${key}: ${typeof item === "number" ? countText(item) : typeof item === "string" ? item : "Unavailable"}`).join(" · ");
}

