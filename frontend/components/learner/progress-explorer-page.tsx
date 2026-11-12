"use client";

import { useCallback, useState } from "react";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { LearnerPageHeading, ResearchDataNotice, SelectedLearnerSummary, SelectedRecordRequired } from "@/components/learner/learner-page-common";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import { evidenceService } from "@/lib/services/evidence.service";
import { learnerStateService } from "@/lib/services/learner-state.service";
import { loadLatestIndexedPage } from "@/lib/learner/data";
import { artifactResourceKey, evidenceForConcept, formatCount, formatInterval, formatPercentage, readNumber, readString, readStringList, readableStatus, selectedConcept } from "@/lib/learner/presentation";
import type { ApiPage, BehavioralStateRecord, EvidenceRecord, JsonObject, LearnerDetail } from "@/lib/api/types";
import type { ApiResourceState } from "@/hooks/use-api-resource";

export function ProgressExplorerPage({ variant }: { variant: "progress" | "learner-state" }) {
  const { learner } = useLearnerSelection();
  if (!learner) return <SelectedRecordRequired/>;
  return <ProgressExplorerForLearner key={learner.learner_id} learner={learner} variant={variant}/>;
}

function ProgressExplorerForLearner({ learner, variant }: { learner: LearnerDetail; variant: "progress" | "learner-state" }) {
  const { learner_id: learnerId, available_data: availableData } = learner;
  const stateKey = artifactResourceKey(learnerId, availableData, "phase9_states");
  const evidenceKey = artifactResourceKey(learnerId, availableData, "phase10_evidence");
  const loadState = useCallback((signal: AbortSignal) => learnerStateService.get(learnerId, signal), [learnerId]);
  const loadEvidence = useCallback((signal: AbortSignal) => loadLatestIndexedPage(
    (query) => evidenceService.list(learnerId, query), 100, signal,
  ), [learnerId]);
  const state = useApiResource<BehavioralStateRecord>(stateKey, loadState);
  const evidence = useApiResource<ApiPage<EvidenceRecord>>(evidenceKey, loadEvidence);
  const [selectedConceptId, setSelectedConceptId] = useState("");

  return <div className="learner-experience-page">
    <LearnerPageHeading eyebrow={variant === "progress" ? "LEARNING STUDIO" : "OBSERVED BEHAVIOR"} title={variant === "progress" ? "Learning progress" : "Behavioral observations"} description="Review recorded response outcomes, concept-level counts, and the limits of each available estimate."/>
    <SelectedLearnerSummary learner={learner}/>

    <section className="panel learner-progress-panel">
      <SectionHeading eyebrow="Phase 9 snapshot" title="Observed response summary" detail="Historical response statistics are not direct evidence of understanding."/>
      <ApiResourcePanel resource={state.resource} retry={state.retry} loadingLabel="Loading response history" emptyTitle="No behavioral snapshot" emptyMessage="This learner record does not have a Phase 9 behavioral state.">
        {(record, requestId) => <ApiDataBoundary requestId={requestId}><BehaviorMetrics record={record}/></ApiDataBoundary>}
      </ApiResourcePanel>
    </section>

    <section className="learner-progress-layout">
      <div className="panel concept-list-panel">
        <SectionHeading eyebrow="Concept explorer" title="Observed skill tags" detail="EdNet skill IDs are dataset tags, not validated prerequisite concepts."/>
        <ApiResourcePanel resource={state.resource} retry={state.retry} loadingLabel="Loading concept-level response records" emptyTitle="No concepts are available" emptyMessage="No concept-level behavior was returned for this learner.">
        {(record, requestId) => <ApiDataBoundary requestId={requestId}><ConceptList concepts={record.concept_states} selectedId={selectedConceptId} onSelect={setSelectedConceptId}/></ApiDataBoundary>}
        </ApiResourcePanel>
      </div>
      <div className="panel concept-detail-panel">
        <SectionHeading eyebrow="Selected concept" title="Evidence and uncertainty" detail="Select a skill tag to inspect its returned statistics and matching indexed evidence."/>
        <ApiResourcePanel resource={state.resource} retry={state.retry} loadingLabel="Loading selected concept" emptyTitle="Concept detail unavailable" emptyMessage="Select a record with a behavioral snapshot to inspect concept-level information.">
          {(record, requestId) => <ApiDataBoundary requestId={requestId}><ConceptDetail concepts={record.concept_states} selectedId={selectedConceptId} evidence={evidence.resource} retryEvidence={evidence.retry}/></ApiDataBoundary>}
        </ApiResourcePanel>
      </div>
    </section>

    <section className="panel learner-evidence-panel">
      <SectionHeading eyebrow="Phase 10 evidence" title="Indexed evidence records" detail="Evidence provenance and processing notes travel with each record."/>
      <ApiResourcePanel resource={evidence.resource} retry={evidence.retry} loadingLabel="Loading evidence index" emptyTitle="No evidence records" emptyMessage="No Phase 10 evidence is indexed for this learner record.">
        {(page, requestId) => <ApiDataBoundary requestId={requestId}><EvidenceList page={page}/></ApiDataBoundary>}
      </ApiResourcePanel>
    </section>

    <ResearchDataNotice>Recent-window and event-time fields come from the saved source records. EdNet timestamps are shifted question-given times rather than real-world response times. No trend line is drawn because the API supplies a snapshot, not a time series.</ResearchDataNotice>
  </div>;
}

function BehaviorMetrics({ record }: { record: BehavioralStateRecord }) {
  const summary = record.observation_summary;
  const performance = record.learning_performance;
  const metrics: [string, string][] = [
    ["Recorded interactions", formatCount(readNumber(summary, "total_interactions"))],
    ["Labelled responses", formatCount(readNumber(summary, "labelled_responses"))],
    ["Unlabelled interactions", formatCount(readNumber(summary, "unlabelled_interactions"))],
    ["Correct responses", formatCount(readNumber(performance, "correct"))],
    ["Incorrect responses", formatCount(readNumber(performance, "incorrect"))],
    ["Historical correctness", formatPercentage(readNumber(performance, "historical_performance"))],
    ["Recent correctness", formatPercentage(readNumber(performance, "recent_performance"))],
    ["Smoothed response estimate", formatPercentage(readNumber(performance, "estimated_performance"))],
  ];
  return <div className="learner-progress-summary">
    <div className="learner-metric-grid learner-metric-grid--wide">{metrics.map(([label, value]) => <div className="learner-metric" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
    <div className="learner-progress-qualifiers"><span>Trend <strong>{readableStatus(readString(performance, "performance_trend"))}</strong></span><span>Evidence sufficiency <strong>{readableStatus(readString(performance, "evidence_sufficiency"))}</strong></span><span>Estimate confidence <strong>{readableStatus(readString(performance, "estimate_confidence"))}</strong></span><span>Reported 95% interval <strong>{formatInterval(performance.uncertainty_interval_95)}</strong></span></div>
    <ul className="learner-limitations-list">{record.limitations.slice(0, 4).map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
  </div>;
}

function ConceptList({ concepts, selectedId, onSelect }: { concepts: JsonObject[]; selectedId: string; onSelect: (id: string) => void }) {
  if (!concepts.length) return <EmptyState title="No concept records">The API returned no concept-level response summaries.</EmptyState>;
  return <ul className="concept-record-list" aria-label="Observed skill tags">
    {concepts.map((concept, index) => {
      const id = readString(concept, "concept_id");
      if (!id) return null;
      const attempts = readNumber(concept, "attempts");
      const active = selectedId ? selectedId === id : index === 0;
      return <li key={id}><button className={`concept-record-button ${active ? "concept-record-button--active" : ""}`} type="button" onClick={() => onSelect(id)} aria-pressed={active}>
        <span className="concept-record-copy"><strong>{id}</strong><small>{formatCount(attempts)} recorded attempts · {readableStatus(readString(concept, "performance_trend"))}</small></span>
        <span className="concept-record-score">{formatPercentage(readNumber(concept, "historical_accuracy"))}</span>
      </button></li>;
    })}
  </ul>;
}

function ConceptDetail({ concepts, selectedId, evidence, retryEvidence }: { concepts: JsonObject[]; selectedId: string; evidence: ApiResourceState<ApiPage<EvidenceRecord>>; retryEvidence: () => void }) {
  const concept = selectedConcept(concepts, selectedId);
  if (!concept) return <EmptyState title="Choose a concept tag">Select an observed skill tag to see its counts and available evidence.</EmptyState>;
  const id = readString(concept, "concept_id");
  if (!id) return <EmptyState title="Concept identifier not reported">The backend returned a concept record without an identifier.</EmptyState>;
  const matching = evidence.status === "success" && evidence.data ? evidenceForConcept(evidence.data.items, id) : [];
  const interval = concept.uncertainty_interval_95;
  return <div className="concept-selected-detail">
    <div className="concept-selected-title"><span className="eyebrow">EDNET SKILL TAG</span><strong>{id}</strong><StatusBadge tone="amber">Not a validated concept</StatusBadge></div>
    <div className="concept-detail-metrics"><Metric label="Attempts" value={formatCount(readNumber(concept, "attempts"))}/><Metric label="Correct" value={formatCount(readNumber(concept, "correct"))}/><Metric label="Incorrect" value={formatCount(readNumber(concept, "incorrect"))}/><Metric label="Evidence count" value={formatCount(readNumber(concept, "evidence_count"))}/><Metric label="Historical correctness" value={formatPercentage(readNumber(concept, "historical_accuracy"))}/><Metric label="Recent correctness" value={formatPercentage(readNumber(concept, "recent_accuracy"))}/><Metric label="Smoothed response estimate" value={formatPercentage(readNumber(concept, "smoothed_performance"))}/><Metric label="Reported 95% interval" value={formatInterval(interval)}/></div>
    <div className="concept-detail-qualifiers"><span>Evidence sufficiency <strong>{readableStatus(readString(concept, "evidence_sufficiency"))}</strong></span><span>Uncertainty <strong>{readableStatus(readString(concept, "uncertainty_level"))}</strong></span><span>Trend <strong>{readableStatus(readString(concept, "performance_trend"))}</strong></span></div>
    <div className="concept-issues"><strong>Reported potential issues</strong><span>{readStringList(concept, "potential_issues").join(" · ") || "None reported"}</span><strong>Uncertainty reasons</strong><span>{readStringList(concept, "uncertainty_reason").join(" · ") || "None reported"}</span></div>
    <div className="concept-supporting-evidence"><strong>Matching evidence in the loaded index page</strong>
      {evidence.status === "loading" && <span>Loading indexed evidence…</span>}
      {evidence.status === "error" && <button type="button" className="text-link" onClick={retryEvidence}>Retry evidence lookup</button>}
      {evidence.status === "idle" && <span>No evidence endpoint data is available for this record.</span>}
      {evidence.status === "success" && <ApiDataBoundary requestId={evidence.requestId}>{matching.length === 0 ? <span>No matching record was found in the displayed evidence page. The behavioral evidence count above is preserved as returned.</span> : matching.map((record) => <EvidenceDetailRow record={record} key={record.evidence_id}/>)}</ApiDataBoundary>}
    </div>
  </div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="learner-metric"><span>{label}</span><strong>{value}</strong></div>;
}

function EvidenceList({ page }: { page: ApiPage<EvidenceRecord> }) {
  if (!page.items.length) return <EmptyState title="No evidence records returned">The API returned an empty evidence page.</EmptyState>;
  return <div className="learner-evidence-list"><div className="evidence-page-note">Showing {page.items.length} of {page.total.toLocaleString()} indexed records. The page is selected from the latest source-event positions.</div>{page.items.slice().reverse().map((record) => <EvidenceDetailRow record={record} key={record.evidence_id}/>)}</div>;
}

function EvidenceDetailRow({ record }: { record: EvidenceRecord }) {
  const skills = record.content.skill_ids;
  const skillIds = Array.isArray(skills) ? skills.filter((value): value is string => typeof value === "string") : [];
  return <article className="learner-evidence-detail-row">
    <div className="learner-evidence-row-heading"><div><span className="evidence-type-mark">{record.evidence_type === "interaction" ? "Q" : "E"}</span><div><strong>{record.evidence_type === "interaction" ? "Recorded interaction" : record.evidence_type.replaceAll("_", " ")}</strong><span>{record.provenance.source_dataset} · sequence {record.temporal.sequence_number ?? "not supplied"}</span></div></div><StatusBadge tone={record.processing.status === "processed" ? "teal" : "amber"}>{readableStatus(record.processing.status)}</StatusBadge></div>
    <dl className="evidence-provenance-grid"><div><dt>Source record</dt><dd>{record.provenance.source_record_id ?? "Not supplied"}</dd></div><div><dt>Source modality</dt><dd>{record.provenance.source_modality}</dd></div><div><dt>Timestamp meaning</dt><dd>{record.temporal.timestamp_source ?? "Not supplied"}</dd></div><div><dt>Temporal precision</dt><dd>{record.temporal.temporal_precision}</dd></div><div><dt>Skill tags</dt><dd>{skillIds.join(", ") || "Not supplied"}</dd></div><div><dt>Processing version</dt><dd>{record.provenance.processing_version}</dd></div></dl>
    {(record.uncertainty.flags.length > 0 || record.uncertainty.notes.length > 0) && <p className="evidence-uncertainty-note">{[...record.uncertainty.flags, ...record.uncertainty.notes].join(" · ")}</p>}
  </article>;
}
