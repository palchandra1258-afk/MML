"use client";

import Link from "next/link";
import { useCallback } from "react";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { LearnerRecordPicker } from "@/components/learner/learner-record-picker";
import { LearnerPageHeading, ResearchDataNotice, SelectedLearnerSummary } from "@/components/learner/learner-page-common";
import { useApiResource } from "@/hooks/use-api-resource";
import { useApiHealth } from "@/hooks/use-api-health";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import type { ApiPage, BehavioralStateRecord, CognitiveStateRecord, EvidenceRecord, HealthData, LearnerDetail, RepresentationRecord, TrajectoryRecord } from "@/lib/api/types";
import { cognitiveStateService } from "@/lib/services/cognitive-state.service";
import { evidenceService } from "@/lib/services/evidence.service";
import { learnerStateService } from "@/lib/services/learner-state.service";
import { representationService } from "@/lib/services/representation.service";
import { trajectoryService } from "@/lib/services/trajectory.service";
import { artifactResourceKey, formatCount, formatInterval, formatPercentage, readNumber, readString, readStringList, readableStatus } from "@/lib/learner/presentation";
import { loadLatestIndexedPage } from "@/lib/learner/data";

function SelectedRecordOverview() {
  const { learner } = useLearnerSelection();
  if (!learner) {
    return <EmptyState title="Choose a learner record to begin">The dashboard shows saved behavioral and research records only after you select a pseudonymous learner record above. It does not identify a signed-in learner.</EmptyState>;
  }
  return <SelectedRecordData key={learner.learner_id} learner={learner}/>;
}

function SelectedRecordData({ learner }: { learner: LearnerDetail }) {
  const { learner_id: learnerId, available_data: availableData, trajectory_count: trajectoryCount } = learner;
  const stateKey = artifactResourceKey(learnerId, availableData, "phase9_states");
  const cognitiveKey = artifactResourceKey(learnerId, availableData, "phase11_states");
  const evidenceKey = artifactResourceKey(learnerId, availableData, "phase10_evidence");
  const planKey = artifactResourceKey(learnerId, availableData, "phase12_plans");
  const trajectoryKey = trajectoryCount > 0 ? `${learnerId}:trajectories` : null;

  const loadState = useCallback((signal: AbortSignal) => learnerStateService.get(learnerId, signal), [learnerId]);
  const loadCognitive = useCallback((signal: AbortSignal) => cognitiveStateService.getLatest(learnerId, signal), [learnerId]);
  const loadEvidence = useCallback((signal: AbortSignal) => loadLatestIndexedPage(
    (query) => evidenceService.list(learnerId, query), 5, signal,
  ), [learnerId]);
  const loadPlans = useCallback((signal: AbortSignal) => loadLatestIndexedPage(
    (query) => representationService.list(learnerId, query), 5, signal,
  ), [learnerId]);
  const loadTrajectories = useCallback((signal: AbortSignal) => trajectoryService.list(learnerId, { limit: 5, offset: 0, signal }), [learnerId]);

  const state = useApiResource<BehavioralStateRecord>(stateKey, loadState);
  const cognitive = useApiResource<CognitiveStateRecord>(cognitiveKey, loadCognitive);
  const evidence = useApiResource<ApiPage<EvidenceRecord>>(evidenceKey, loadEvidence);
  const plans = useApiResource<ApiPage<RepresentationRecord>>(planKey, loadPlans);
  const trajectories = useApiResource<ApiPage<TrajectoryRecord>>(trajectoryKey, loadTrajectories);

  return <div className="learner-record-overview">
    <SelectedLearnerSummary learner={learner}/>
    <div className="learner-overview-grid">
      <section className="panel learner-overview-panel learner-behavior-panel">
        <SectionHeading eyebrow="Observed behavior" title="Response history" detail="Recorded answer outcomes; not a measure of understanding."/>
        <ApiResourcePanel resource={state.resource} retry={state.retry} loadingLabel="Loading behavioral snapshot" emptyTitle="No behavioral snapshot" emptyMessage="The selected record does not include an available Phase 9 behavioral state.">
          {(record, requestId) => <ApiDataBoundary requestId={requestId}>
            <BehaviorSummary record={record}/>
          </ApiDataBoundary>}
        </ApiResourcePanel>
        <Link href="/progress" className="panel-link">Explore progress and concepts <span aria-hidden="true">→</span></Link>
      </section>

      <section className="panel learner-overview-panel">
        <SectionHeading eyebrow="Provisional interpretation" title="Cognitive insights" detail="Rule-based estimates remain uncertain and are not diagnoses."/>
        <ApiResourcePanel resource={cognitive.resource} retry={cognitive.retry} loadingLabel="Loading saved estimate" emptyTitle="No cognitive estimate" emptyMessage="No Phase 11 estimate is available for this record.">
          {(record, requestId) => <ApiDataBoundary requestId={requestId}><CognitivePreview record={record}/></ApiDataBoundary>}
        </ApiResourcePanel>
        <Link href="/cognitive-state" className="panel-link">Review uncertainty and evidence <span aria-hidden="true">→</span></Link>
      </section>

      <section className="panel learner-overview-panel">
        <SectionHeading eyebrow="Indexed evidence" title="Recorded learning evidence" detail="Source-linked records in the backend evidence index."/>
        <ApiResourcePanel resource={evidence.resource} retry={evidence.retry} loadingLabel="Loading evidence records" emptyTitle="No indexed evidence" emptyMessage="No Phase 10 evidence records are available for this learner.">
          {(page, requestId) => <ApiDataBoundary requestId={requestId}><EvidencePreview page={page}/></ApiDataBoundary>}
        </ApiResourcePanel>
        <Link href="/progress" className="panel-link">Inspect concept-linked evidence <span aria-hidden="true">→</span></Link>
      </section>

      <section className="panel learner-overview-panel">
        <SectionHeading eyebrow="Saved learning path" title="Trajectory" detail="Only persisted trajectory records are shown here."/>
        <ApiResourcePanel resource={trajectories.resource} retry={trajectories.retry} loadingLabel="Loading trajectory records" emptyTitle="No trajectory record" emptyMessage="This learner record has no persisted trajectory. No learning goal or step is inferred from response history.">
          {(page, requestId) => <ApiDataBoundary requestId={requestId}><TrajectoryPreview page={page}/></ApiDataBoundary>}
        </ApiResourcePanel>
        <Link href="/trajectory" className="panel-link">Open trajectory details <span aria-hidden="true">→</span></Link>
      </section>

      <section className="learner-overview-plan panel">
        <div className="learner-overview-plan-copy"><span className="eyebrow">LEARNING AVAILABILITY</span><h3>Learning activities are unavailable</h3><p>The backend can return saved representation plans, but it has no content provider or interaction-submission route. No lesson, quiz, or tutoring activity can be launched.</p></div>
        <ApiResourcePanel resource={plans.resource} retry={plans.retry} loadingLabel="Loading saved representation plans" emptyTitle="No representation plan" emptyMessage="No Phase 12 plan is available for this learner.">
          {(page, requestId) => <ApiDataBoundary requestId={requestId}><PlanPreview page={page}/></ApiDataBoundary>}
        </ApiResourcePanel>
      </section>
    </div>
    <ResearchDataNotice>EdNet records are pseudonymous research artifacts. Source timestamps are shifted question-given timestamps, not real-world response times. API records are saved snapshots, not live model inference.</ResearchDataNotice>
  </div>;
}

function BehaviorSummary({ record }: { record: BehavioralStateRecord }) {
  const performance = record.learning_performance;
  const summary = record.observation_summary;
  const interval = performance.uncertainty_interval_95;
  return <div className="learner-behavior-summary">
    <div className="learner-metric-grid">
      <Metric label="Recorded interactions" value={formatCount(readNumber(summary, "total_interactions"))}/>
      <Metric label="Labelled responses" value={formatCount(readNumber(summary, "labelled_responses"))}/>
      <Metric label="Correct responses" value={formatCount(readNumber(performance, "correct"))}/>
      <Metric label="Historical correctness" value={formatPercentage(readNumber(performance, "historical_performance"))}/>
      <Metric label="Recent correctness" value={formatPercentage(readNumber(performance, "recent_performance"))}/>
      <Metric label="Observed concepts" value={formatCount(readNumber(summary, "unique_concepts_observed"))}/>
    </div>
    <div className="learner-inline-facts"><span>Performance trend <strong>{readableStatus(readString(performance, "performance_trend"))}</strong></span><span>Evidence sufficiency <strong>{readableStatus(readString(performance, "evidence_sufficiency"))}</strong></span><span>Reported 95% interval <strong>{formatInterval(interval)}</strong></span></div>
    <p className="learner-subtle-note">The interval concerns response correctness. It does not quantify cognitive-state certainty.</p>
  </div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="learner-metric"><span>{label}</span><strong>{value}</strong></div>;
}

function CognitivePreview({ record }: { record: CognitiveStateRecord }) {
  const first = record.possible_difficulty_hypotheses[0];
  const summary = record.observed_evidence_summary;
  const statement = first ? readString(first, "statement") : undefined;
  return <div className="cognitive-preview">
    <StatusBadge tone="purple">Provisional estimate</StatusBadge>
    <strong className="cognitive-preview-title">{statement ?? "Evidence-supported hypothesis"}</strong>
    <span>{record.possible_difficulty_hypotheses.length ? `${record.possible_difficulty_hypotheses.length} hypotheses in saved estimate` : "No hypotheses were returned"}</span>
    <div className="cognitive-preview-facts"><span>Overall uncertainty <strong>{record.uncertainty.overall_uncertainty}</strong></span><span>Contradictory evidence <strong>{formatCount(readNumber(summary, "contradictory_evidence_count"))}</strong></span><span>Missing modalities <strong>{readStringList(summary, "missing_modalities").join(", ") || "Not reported"}</strong></span></div>
    <p>Confidence is support for a provisional behavioral category, not probability that a cognitive state is true.</p>
  </div>;
}

function EvidencePreview({ page }: { page: ApiPage<EvidenceRecord> }) {
  if (!page.items.length) return <EmptyState title="No evidence records returned">The API reports no indexed evidence for this record.</EmptyState>;
  return <div className="learner-evidence-preview">
    <div className="evidence-page-note">Showing {page.items.length} of {page.total.toLocaleString()} indexed records, ordered by source event time.</div>
    {page.items.slice(-5).reverse().map((record) => <article className="learner-evidence-row" key={record.evidence_id}>
      <span className="evidence-type-mark">{record.evidence_type === "interaction" ? "Q" : "E"}</span>
      <div><strong>{record.evidence_type === "interaction" ? "Recorded interaction" : record.evidence_type.replaceAll("_", " ")}</strong><span>{record.provenance.source_dataset} · sequence {record.temporal.sequence_number ?? "not supplied"}</span><small>{record.uncertainty.flags[0] ?? "No evidence quality flags reported"}</small></div>
      <StatusBadge tone={record.processing.status === "processed" ? "teal" : "amber"}>{readableStatus(record.processing.status)}</StatusBadge>
    </article>)}
  </div>;
}

function TrajectoryPreview({ page }: { page: ApiPage<TrajectoryRecord> }) {
  if (!page.items.length) return <EmptyState title="No trajectory is available">The API returned an empty trajectory index for this learner.</EmptyState>;
  const trajectory = page.items[0];
  return <div className="trajectory-preview"><p className="trajectory-page-note">One saved trajectory from an index of {page.total}.</p><div><StatusBadge tone={trajectory.current_status === "ACTIVE" ? "teal" : "amber"} dot>{readableStatus(trajectory.current_status)}</StatusBadge><strong>{trajectory.primary_learning_goal}</strong><span>{trajectory.current_learning_step || "No current step supplied"}</span></div><div className="trajectory-preview-counts"><span>{trajectory.completed_steps.length} recorded completed steps</span><span>{trajectory.pending_steps.length} pending steps</span></div></div>;
}

function PlanPreview({ page }: { page: ApiPage<RepresentationRecord> }) {
  if (!page.items.length) return <EmptyState title="No plan is available">The API returned an empty representation-plan index.</EmptyState>;
  const plan = page.items[page.items.length - 1];
  const objectiveDescription = readString(plan.learning_objective, "description");
  return <div className="plan-preview"><span className="eyebrow">SAVED PLAN · {plan.concept_id}</span><strong>{plan.decision.selected_action}</strong><span>{objectiveDescription ?? "No learner objective was supplied in this plan."}</span><p>{readableStatus(plan.decision.delivery_status)} · recommendation does not mean content was delivered</p></div>;
}

export function LearnerOverviewDashboard() {
  const { health } = useApiHealth();
  return <div className="learner-experience-page">
    <LearnerPageHeading eyebrow="LEARNING STUDIO" title="Learner overview" description="Explore saved behavioral evidence and provisional estimates for a selected research record."/>
    {health && <BackendReadinessPanel health={health}/>}
    <LearnerRecordPicker/>
    <SelectedRecordOverview/>
  </div>;
}

const serviceModules = [
  ["phase9_behavioral_state", "Behavioral states"],
  ["phase10_evidence", "Evidence records"],
  ["phase10_grouping", "Evidence grouping"],
  ["phase11_cognitive_state", "Cognitive estimates"],
  ["phase12_representation", "Representation plans"],
  ["phase13_trajectory", "Trajectory service"],
  ["model_inference", "Model inference"],
] as const;

function BackendReadinessPanel({ health }: { health: HealthData }) {
  return <section className="panel backend-readiness-panel">
    <div className="backend-readiness-heading"><SectionHeading eyebrow="BACKEND SERVICE READINESS" title="Available research modules" detail="Module status and counts come from the API health response."/><StatusBadge tone={health.status === "healthy" ? "teal" : "amber"} dot>{health.status === "healthy" ? "API healthy" : "API degraded"}</StatusBadge></div>
    <ApiDataBoundary timestamp={health.timestamp}>
      <div className="backend-readiness-summary"><span>API version {health.api_version}</span><span>Database {health.database}</span></div>
      <ul className="backend-module-list">{serviceModules.map(([key, label]) => {
        const moduleStatus = health.modules[key];
        const available = moduleStatus?.available;
        const count = moduleStatus?.record_count;
        const mode = moduleStatus?.mode;
        const ready = available === true;
        return <li className="backend-module-row" key={key}><span className={`module-state-dot ${ready ? "module-state-dot--ready" : "module-state-dot--off"}`} aria-hidden="true"/><span className="backend-module-name"><strong>{label}</strong><small>{typeof mode === "string" ? mode.replaceAll("_", " ") : "Status reported by API"}</small></span><span className="backend-module-count">{typeof count === "number" ? count.toLocaleString() : "—"}</span><span className={`backend-module-status ${ready ? "backend-module-status--ready" : ""}`}>{ready ? "Available" : available === false ? "Unavailable" : "Unknown"}</span></li>;
      })}</ul>
    </ApiDataBoundary>
  </section>;
}
