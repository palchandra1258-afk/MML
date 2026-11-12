"use client";

import { useCallback } from "react";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { LearnerPageHeading, ResearchDataNotice, SelectedLearnerSummary, SelectedRecordRequired } from "@/components/learner/learner-page-common";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import { cognitiveStateService } from "@/lib/services/cognitive-state.service";
import type { CognitiveStateRecord, JsonObject, LearnerDetail } from "@/lib/api/types";
import { artifactResourceKey, formatCount, formatPercentage, readNumber, readString, readStringList, readableStatus } from "@/lib/learner/presentation";

export function CognitiveInsightsPage() {
  const { learner } = useLearnerSelection();
  if (!learner) return <SelectedRecordRequired/>;
  return <CognitiveInsightsForLearner key={learner.learner_id} learner={learner}/>;
}

function CognitiveInsightsForLearner({ learner }: { learner: LearnerDetail }) {
  const loadCognitive = useCallback((signal: AbortSignal) => cognitiveStateService.getLatest(learner.learner_id, signal), [learner.learner_id]);
  const { resource, retry } = useApiResource<CognitiveStateRecord>(
    artifactResourceKey(learner.learner_id, learner.available_data, "phase11_states"),
    loadCognitive,
  );

  return <div className="learner-experience-page">
    <LearnerPageHeading eyebrow="COGNITIVE INTELLIGENCE" title="Cognitive insights" description="Review the latest saved estimate, supporting records, uncertainty, and suggested information-gathering actions."/>
    <SelectedLearnerSummary learner={learner}/>
    <section className="panel cognitive-insights-panel">
      <SectionHeading eyebrow="Phase 11 saved snapshot" title="Provisional estimate" detail="This is a rule-based behavioral category without validated cognitive ground truth."/>
      <ApiResourcePanel resource={resource} retry={retry} loadingLabel="Loading provisional estimate" emptyTitle="No cognitive estimate" emptyMessage="This learner record has no Phase 11 cognitive-state snapshot.">
        {(record, requestId) => <ApiDataBoundary requestId={requestId}><CognitiveStateDetails record={record}/></ApiDataBoundary>}
      </ApiResourcePanel>
    </section>
    <ResearchDataNotice>Confidence describes support for a provisional behavioral category; it is not a probability of cognitive truth. Recommendations are saved outputs. No diagnostic question or lesson can be delivered from this interface.</ResearchDataNotice>
  </div>;
}

function CognitiveStateDetails({ record }: { record: CognitiveStateRecord }) {
  const summary = record.observed_evidence_summary;
  const missing = readStringList(summary, "missing_modalities");
  const available = readStringList(summary, "available_modalities");
  const uncertaintyRows: { label: string; level: string; reasons: string[] }[] = [
    { label: "Evidence", level: record.uncertainty.evidence_uncertainty, reasons: record.uncertainty.uncertainty_reasons.evidence ?? [] },
    { label: "Temporal", level: record.uncertainty.temporal_uncertainty, reasons: record.uncertainty.uncertainty_reasons.temporal ?? [] },
    { label: "Modality", level: record.uncertainty.modality_uncertainty, reasons: record.uncertainty.uncertainty_reasons.modality ?? [] },
    { label: "Inference", level: record.uncertainty.inference_uncertainty, reasons: record.uncertainty.uncertainty_reasons.inference ?? [] },
  ];
  return <div className="cognitive-state-details">
    <header className="cognitive-snapshot-header"><div><StatusBadge tone="purple">Provisional estimate · version {record.state_version}</StatusBadge><h3>{record.cognitive_state_id}</h3><p>Generated {new Date(record.generated_at).toLocaleString()}</p></div><span className="snapshot-schema">Schema {record.schema_version}</span></header>
    <section className="cognitive-evidence-summary">
      <div className="learner-metric-grid learner-metric-grid--wide">
        <Metric label="Interaction events" value={formatCount(readNumber(summary, "interaction_event_count"))}/>
        <Metric label="Labelled responses" value={formatCount(readNumber(summary, "labelled_response_count"))}/>
        <Metric label="Historical correctness" value={formatPercentage(readNumber(summary, "historical_correctness"))}/>
        <Metric label="Recent correctness" value={formatPercentage(readNumber(summary, "recent_correctness"))}/>
        <Metric label="Contradictory evidence" value={formatCount(readNumber(summary, "contradictory_evidence_count"))}/>
        <Metric label="Evidence references" value={formatCount(record.evidence_references.length)}/>
      </div>
      <div className="modality-availability"><div><span>Available modalities</span><strong>{available.join(", ") || "Not reported"}</strong></div><div><span>Missing modalities</span><strong>{missing.join(", ") || "None reported"}</strong></div></div>
    </section>

    <section className="cognitive-uncertainty-section" aria-labelledby="uncertainty-heading">
      <div className="subsection-heading"><div><p className="eyebrow">UNCERTAINTY PROFILE</p><h3 id="uncertainty-heading">Uncertainty remains visible</h3></div><StatusBadge tone="amber">Overall {readableStatus(record.uncertainty.overall_uncertainty)}</StatusBadge></div>
      <div className="uncertainty-grid">{uncertaintyRows.map(({ label, level, reasons }) => <div className="uncertainty-item" key={label}><span>{label} uncertainty</span><strong>{readableStatus(level)}</strong><p>{reasons.join(" ") || "No reason supplied."}</p></div>)}</div>
    </section>

    <section className="cognitive-hypotheses-section">
      <SectionHeading eyebrow="EVIDENCE-SUPPORTED HYPOTHESES" title="Possible difficulty hypotheses" detail="Each item is a provisional rule output, not a diagnosis."/>
      {record.possible_difficulty_hypotheses.length === 0 ? <EmptyState title="No hypotheses returned">The saved estimate contains no possible difficulty hypotheses.</EmptyState> : <div className="hypothesis-list">{record.possible_difficulty_hypotheses.map((hypothesis, index) => <HypothesisCard hypothesis={hypothesis} index={index} key={readString(hypothesis, "hypothesis_id") ?? `${readString(hypothesis, "concept_id") ?? "hypothesis"}-${index}`}/>)}</div>}
    </section>

    <section className="cognitive-estimates-section">
      <SectionHeading eyebrow="CONCEPT ESTIMATES" title="Observed pattern categories" detail="The status is based on response evidence and keeps the backend’s confidence scope."/>
      {record.concept_estimates.length === 0 ? <EmptyState title="No concept estimates returned">The saved estimate contains no concept-level categories.</EmptyState> : <div className="estimate-table-wrap"><table className="estimate-table"><thead><tr><th scope="col">Skill tag</th><th scope="col">Provisional status</th><th scope="col">Support</th><th scope="col">Uncertainty</th><th scope="col">Rationale</th></tr></thead><tbody>{record.concept_estimates.map((estimate, index) => <tr key={`${readString(estimate, "concept_id") ?? "estimate"}-${index}`}><th scope="row">{readString(estimate, "concept_id") ?? "Not reported"}</th><td>{readableStatus(readString(estimate, "estimated_learning_status"))}</td><td>{readableStatus(readString(estimate, "estimate_confidence"))}</td><td>{readableStatus(readString(estimate, "uncertainty_level"))}</td><td>{readString(estimate, "rationale") ?? "Not reported"}<small>{readString(estimate, "confidence_scope") ?? "Confidence scope not supplied."}</small></td></tr>)}</tbody></table></div>}
    </section>

    <section className="diagnostic-recommendations-section">
      <SectionHeading eyebrow="SAVED RECOMMENDATIONS" title="Additional evidence suggested" detail="Recommendations are not executable activities in the current API."/>
      {record.diagnostic_recommendations.length === 0 ? <EmptyState title="No diagnostic recommendations">No additional evidence-gathering recommendation was returned.</EmptyState> : <div className="recommendation-list">{record.diagnostic_recommendations.map((item, index) => <article className="recommendation-item" key={readString(item, "recommendation_id") ?? `recommendation-${index}`}><span className="recommendation-marker" aria-hidden="true">+</span><div><strong>{readString(item, "concept_id") ?? "Concept not supplied"} · {readableStatus(readString(item, "action"))}</strong><p>{readString(item, "reason") ?? "No rationale supplied."}</p><span>Status: {readableStatus(readString(item, "status"))}</span></div><StatusBadge tone="amber">Not deliverable</StatusBadge></article>)}</div>}
    </section>

    <section className="cognitive-references-section">
      <SectionHeading eyebrow="PROVENANCE" title="Supporting evidence references" detail="The estimate links to source evidence; not every linked item is necessarily available in the separate evidence index."/>
      {record.evidence_references.length === 0 ? <EmptyState title="No evidence references returned">No supporting source references were attached to this estimate.</EmptyState> : <div className="reference-list">{record.evidence_references.map((reference, index) => <EvidenceReference reference={reference} key={readString(reference, "evidence_id") ?? `reference-${index}`}/>)}</div>}
      {readStringList(summary, "contradictory_evidence_ids").length > 0 && <p className="contradiction-note">Contradictory evidence IDs: {readStringList(summary, "contradictory_evidence_ids").join(", ")}</p>}
    </section>
    <p className="cognitive-limitation">{record.limitations.join(" ")}</p>
  </div>;
}

function HypothesisCard({ hypothesis, index }: { hypothesis: JsonObject; index: number }) {
  return <article className="hypothesis-card"><div className="hypothesis-card-top"><div><span className="hypothesis-index">{String(index + 1).padStart(2, "0")}</span><strong>{readString(hypothesis, "concept_id") ?? "Concept not reported"}</strong></div><StatusBadge tone="amber">{readableStatus(readString(hypothesis, "confidence_or_support_level"))} support</StatusBadge></div><p>{readString(hypothesis, "statement") ?? "No hypothesis statement supplied."}</p><div className="hypothesis-meta"><span>Type: {readableStatus(readString(hypothesis, "hypothesis_type"))}</span><span>Investigation: {readableStatus(readString(hypothesis, "investigation_status"))}</span></div><div className="hypothesis-evidence"><span>Supporting IDs: {readStringList(hypothesis, "supporting_evidence_ids").join(", ") || "None supplied"}</span><span>Contradictory IDs: {readStringList(hypothesis, "contradictory_evidence_ids").join(", ") || "None supplied"}</span></div>{readStringList(hypothesis, "uncertainty_reason").length > 0 && <small>{readStringList(hypothesis, "uncertainty_reason").join(" · ")}</small>}</article>;
}

function EvidenceReference({ reference }: { reference: JsonObject }) {
  return <article className="cognitive-evidence-reference"><span className="evidence-type-mark">E</span><div><strong>{readString(reference, "evidence_id") ?? "Evidence ID not supplied"}</strong><span>{readString(reference, "evidence_type") ?? "type not supplied"} · {readString(reference, "source_dataset") ?? "dataset not supplied"}</span><small>{readString(reference, "source_file") ?? "Source file not supplied"}</small></div><span>Sequence {readNumber(reference, "sequence_number") ?? "not supplied"}</span></article>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="learner-metric"><span>{label}</span><strong>{value}</strong></div>;
}
