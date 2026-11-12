"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { LearnerPageHeading, ResearchDataNotice, SelectedLearnerSummary, SelectedRecordRequired } from "@/components/learner/learner-page-common";
import { EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import type { ApiPage, LearnerDetail, OpenRecord, TrajectoryRecord } from "@/lib/api/types";
import { loadLatestIndexedPage } from "@/lib/learner/data";
import { formatCount, readString, readStringList, readableStatus, selectedTrajectory } from "@/lib/learner/presentation";
import { trajectoryService } from "@/lib/services/trajectory.service";

const PAGE_SIZE = 20;

export function TrajectoryPage() {
  const { learner } = useLearnerSelection();
  if (!learner) return <SelectedRecordRequired/>;
  return <TrajectoryPageForLearner key={learner.learner_id} learnerId={learner.learner_id} trajectoryCount={learner.trajectory_count} learner={learner}/>;
}

function TrajectoryPageForLearner({ learnerId, trajectoryCount, learner }: { learnerId: string; trajectoryCount: number; learner: LearnerDetail }) {
  const [offset, setOffset] = useState(0);
  const [selectedId, setSelectedId] = useState("");
  const loadTrajectories = useCallback((signal: AbortSignal) => trajectoryService.list(learnerId, { limit: PAGE_SIZE, offset, signal }), [learnerId, offset]);
  const trajectories = useApiResource<ApiPage<TrajectoryRecord>>(trajectoryCount > 0 ? `${learnerId}:trajectories:${offset}` : null, loadTrajectories);
  const trajectoryPage = trajectories.resource.status === "success" ? trajectories.resource.data : undefined;
  const selected = trajectoryPage ? selectedTrajectory(trajectoryPage.items, selectedId) : undefined;

  const activeTrajectoryId = selected?.trajectory_id ?? null;
  const activeDiversionId = selected?.orchestration.active_diversion_id ?? null;
  const loadHistory = useCallback((signal: AbortSignal) => loadLatestIndexedPage(
    (query) => trajectoryService.history(learnerId, activeTrajectoryId!, { limit: 100, ...query }), 100, signal,
  ), [activeTrajectoryId, learnerId]);
  const history = useApiResource<ApiPage<OpenRecord>>(activeTrajectoryId ? `${learnerId}:history:${activeTrajectoryId}` : null, loadHistory);

  const loadDiversions = useCallback((signal: AbortSignal) => loadLatestIndexedPage(
    (query) => trajectoryService.listDiversions(learnerId, { limit: 20, ...query }), 20, signal,
  ), [learnerId]);
  const diversions = useApiResource<ApiPage<OpenRecord>>(`${learnerId}:diversions`, loadDiversions);
  const loadActiveDiversion = useCallback((signal: AbortSignal) => trajectoryService.getDiversion(learnerId, activeDiversionId!, signal), [activeDiversionId, learnerId]);
  const activeDiversionListed = diversions.resource.status === "success"
    && diversions.resource.data?.items.some((item) => readString(item, "diversion_id") === activeDiversionId);
  const shouldFetchReferencedDiversion = Boolean(activeDiversionId && diversions.resource.status === "success" && !activeDiversionListed);
  const referencedDiversion = useApiResource<OpenRecord>(shouldFetchReferencedDiversion ? `${learnerId}:diversion:${activeDiversionId}` : null, loadActiveDiversion);

  return <div className="learner-experience-page">
    <LearnerPageHeading eyebrow="LEARNING STUDIO" title="Learning trajectory" description="Review persisted goals, step records, context references, diversions, and trajectory history."/>
    <SelectedLearnerSummary learner={learner}/>

    <section className="panel trajectory-records-panel">
      <SectionHeading eyebrow="PERSISTED TRAJECTORY" title="Trajectory record" detail="A stored path is system state; it does not confirm that a learner completed an activity."/>
      <ApiResourcePanel resource={trajectories.resource} retry={trajectories.retry} loadingLabel="Loading trajectory records" emptyTitle="No persisted trajectory" emptyMessage="This learner record has no trajectory in the application store. A learning goal is not inferred from response history.">
        {(page, requestId) => <ApiDataBoundary requestId={requestId}>
          <div className="trajectory-index-controls">
            <label htmlFor="trajectory-record-select">Choose a trajectory record</label>
            <select id="trajectory-record-select" value={selected?.trajectory_id ?? ""} onChange={(event) => setSelectedId(event.target.value)}>
              {page.items.map((item) => <option value={item.trajectory_id} key={item.trajectory_id}>{item.trajectory_id} · {readableStatus(item.current_status)}</option>)}
            </select>
            {page.total > PAGE_SIZE && <div className="learner-index-pagination"><button type="button" className="button button--secondary" disabled={page.offset === 0 || trajectories.resource.status === "loading"} onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}>Previous</button><span>{page.offset + 1}–{Math.min(page.offset + page.items.length, page.total)} of {page.total}</span><button type="button" className="button button--secondary" disabled={!page.has_more || trajectories.resource.status === "loading"} onClick={() => setOffset((value) => value + PAGE_SIZE)}>Next</button></div>}
          </div>
          {selected ? <TrajectoryRecordDetails record={selected}/> : <EmptyState title="No trajectory on this page">The API returned an empty trajectory page.</EmptyState>}
        </ApiDataBoundary>}
      </ApiResourcePanel>
    </section>

    {selected && shouldFetchReferencedDiversion && <section className="panel trajectory-active-diversion-panel">
      <SectionHeading eyebrow="SAVED ACTIVE REFERENCE" title="Referenced active diversion" detail={`Trajectory ${selected.trajectory_id} stores active diversion ID ${activeDiversionId}. The API is queried for that exact saved record.`}/>
      <ApiResourcePanel resource={referencedDiversion.resource} retry={referencedDiversion.retry} loadingLabel="Loading referenced diversion" emptyTitle="Active diversion record unavailable" emptyMessage="The trajectory has an active diversion reference, but no matching saved snapshot was returned.">
        {(diversion, requestId) => <ApiDataBoundary requestId={requestId}><DiversionCard diversion={diversion} activeForSelectedTrajectory/></ApiDataBoundary>}
      </ApiResourcePanel>
    </section>}

    {selected && <section className="panel trajectory-history-panel">
      <SectionHeading eyebrow="APPEND-ONLY EVENTS" title="Trajectory history" detail="Events are saved transitions and explanations, not a live activity log."/>
      <ApiResourcePanel resource={history.resource} retry={history.retry} loadingLabel="Loading trajectory history" emptyTitle="No history events returned" emptyMessage="The selected trajectory has no saved history events.">
        {(page, requestId) => <ApiDataBoundary requestId={requestId}><HistoryList page={page}/></ApiDataBoundary>}
      </ApiResourcePanel>
    </section>}

    <section className="panel trajectory-diversions-panel">
      <SectionHeading eyebrow="PRESERVED CONTEXT" title="Diversions and resumption records" detail="Only saved diversion snapshots are shown. This screen does not apply actions or resume a trajectory."/>
      <ApiResourcePanel resource={diversions.resource} retry={diversions.retry} loadingLabel="Loading diversion records" emptyTitle="No diversion records" emptyMessage="No diversion snapshot is available for this learner record.">
      {(page, requestId) => <ApiDataBoundary requestId={requestId}><DiversionList page={page} activeDiversionId={activeDiversionId}/></ApiDataBoundary>}
      </ApiResourcePanel>
    </section>
    <ResearchDataNotice>The API supports trajectory creation and the actions activate, pause, and advance_step, but this screen issues no writes. It exposes no diversion mutation or resumption action, and there is no content delivery or interaction outcome endpoint. Context snapshot IDs are references because no context snapshot retrieval route is exposed.</ResearchDataNotice>
  </div>;
}

function TrajectoryRecordDetails({ record }: { record: TrajectoryRecord }) {
  return <div className="trajectory-record-details">
    <header className="trajectory-record-header"><div><span className="eyebrow">{record.trajectory_id} · VERSION {record.trajectory_version}</span><h3>{record.primary_learning_goal}</h3><p>Target tag: {record.target_concept_id} · current tag: {record.current_concept_id}</p></div><StatusBadge tone={record.current_status === "ACTIVE" ? "teal" : "amber"} dot>{readableStatus(record.current_status)}</StatusBadge></header>
    <p className="trajectory-current-step"><span>Current recorded step</span><strong>{record.current_learning_step || "Not supplied"}</strong></p>
    <div className="trajectory-record-counts"><span><strong>{formatCount(record.completed_steps.length)}</strong> completed-step records</span><span><strong>{formatCount(record.pending_steps.length)}</strong> pending-step records</span><span><strong>{formatCount(record.expected_progression.length)}</strong> expected progression records</span></div>
    <div className="trajectory-steps-grid"><StepList title="Completed step records" steps={record.completed_steps}/><StepList title="Pending step records" steps={record.pending_steps}/></div>
    <ExpectedProgression steps={record.expected_progression}/>
    <div className="trajectory-context-grid">
      <ContextValue label="Learning objectives" value={record.learning_objectives.join(" · ") || "None supplied"}/>
      <ContextValue label="Prerequisites in saved record" value={record.prerequisites.join(" · ") || "None supplied"}/>
      <ContextValue label="Supporting evidence IDs" value={record.context.supporting_evidence_ids.join(", ") || "None supplied"} href={record.context.supporting_evidence_ids.length ? "/evidence" : undefined} linkLabel="Open learner evidence explorer"/>
      <ContextValue label="Previous cognitive state" value={record.context.previous_cognitive_state_id ?? "None supplied"} href={record.context.previous_cognitive_state_id ? "/cognitive-state" : undefined} linkLabel="Open learner cognitive view"/>
      <ContextValue label="Previous representation plan" value={record.context.previous_representation_plan_id ?? "None supplied"} href={record.context.previous_representation_plan_id ? "/representations" : undefined} linkLabel="Open learner plan explorer"/>
      <ContextValue label="Active diversion reference" value={record.orchestration.active_diversion_id ?? "None supplied"}/>
      <ContextValue label="Parent trajectory reference" value={record.orchestration.parent_trajectory_id ?? "None supplied"}/>
      <ContextValue label="Saved history reference" value={record.orchestration.transition_history_reference}/>
      <ContextValue label="Learning history reference" value={record.context.learning_history_reference ?? "None supplied"}/>
      <ContextValue label="Prior intervention records" value={formatCount(record.context.previous_interventions.length)}/>
    </div>
    <nav className="trajectory-related-links" aria-label="Inspect related learner records">
      <div><strong>Continue inspecting this learner record</strong><span>Navigation retains the selected research record. Cross-page views are learner-scoped; matching learner IDs do not establish a causal or chronological link.</span></div>
      <div className="trajectory-related-link-list"><Link href="/learner-state">Behavioral state</Link><Link href="/cognitive-state">Cognitive insights</Link><Link href="/representations">Representation plans</Link><Link href="/evidence">Evidence records</Link><Link href="/learning">Saved learning context</Link></div>
    </nav>
    <div className="trajectory-downstream-limits"><strong>Intervention, outcome, and updated state</strong><p>The stored trajectory is available, but this API does not expose content delivery, learner response submission, an intervention receipt, or an outcome-linked state update. No downstream event is inferred here.</p></div>
    <p className="trajectory-record-timestamps">Created {record.created_at} · Updated {record.updated_at}</p>
  </div>;
}

function StepList({ title, steps }: { title: string; steps: string[] }) {
  return <section className="trajectory-step-list"><h4>{title}</h4>{steps.length ? <ul>{steps.map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}</ul> : <p>No step records supplied.</p>}</section>;
}

function ExpectedProgression({ steps }: { steps: TrajectoryRecord["expected_progression"] }) {
  if (!steps.length) return <p className="trajectory-progression-empty">No expected progression records were supplied.</p>;
  return <section className="trajectory-progression"><h4>Expected progression in the saved record</h4><ol>{steps.map((step) => <li key={step.step_id}><span className={`progression-status progression-status--${step.status}`}>{readableStatus(step.status)}</span><div><strong>{step.objective}</strong><small>{step.concept_id} · {step.step_id}</small></div></li>)}</ol><p>These are stored trajectory expectations, not completed learning activities.</p></section>;
}

function ContextValue({ label, value, href, linkLabel }: { label: string; value: string; href?: string; linkLabel?: string }) {
  return <div><dt>{label}</dt><dd>{value}{href && linkLabel && <Link href={href} className="trajectory-context-link">{linkLabel}</Link>}</dd></div>;
}

function HistoryList({ page }: { page: ApiPage<OpenRecord> }) {
  if (!page.items.length) return <EmptyState title="No trajectory history returned">The API returned an empty event page.</EmptyState>;
  return <div className="trajectory-event-list"><p className="trajectory-page-note">Showing {page.items.length} of {page.total} events, newest returned event first.</p>{[...page.items].reverse().map((event, index) => <article className="trajectory-event" key={readString(event, "event_id") ?? `${readString(event, "event_type") ?? "event"}-${index}`}>
    <span className="trajectory-event-marker" aria-hidden="true">{String(page.total - index).padStart(2, "0")}</span>
    <div><div className="trajectory-event-heading"><strong>{readableStatus(readString(event, "event_type"))}</strong><time>{readString(event, "occurred_at") ?? "Time not supplied"}</time></div><p>{readString(event, "decision_explanation") ?? "No event explanation supplied."}</p><div className="trajectory-event-details"><span>State: {readableStatus(readString(event, "previous_state"))} → {readableStatus(readString(event, "new_state"))}</span><span>Trigger: {readString(event, "trigger") ?? "Not supplied"}</span></div><small>Supporting evidence: {readStringList(event, "supporting_evidence_ids").join(", ") || "None supplied"}{readString(event, "related_diversion_id") ? ` · Diversion ${readString(event, "related_diversion_id")}` : ""}</small></div>
  </article>)}</div>;
}

function DiversionList({ page, activeDiversionId }: { page: ApiPage<OpenRecord>; activeDiversionId: string | null }) {
  if (!page.items.length) return <EmptyState title="No saved diversion" >No diversion snapshot is available. No prerequisite relationship is inferred by the interface.</EmptyState>;
  return <div className="trajectory-diversion-list">{page.items.map((diversion, index) => <DiversionCard diversion={diversion} activeForSelectedTrajectory={readString(diversion, "diversion_id") === activeDiversionId} key={readString(diversion, "diversion_id") ?? `diversion-${index}`}/>)}</div>;
}

function DiversionCard({ diversion, activeForSelectedTrajectory = false }: { diversion: OpenRecord; activeForSelectedTrajectory?: boolean }) {
  const evidenceIds = readStringList(diversion, "supporting_evidence_ids");
  const progress = Array.isArray(diversion.progress_history) ? diversion.progress_history : [];
  const revisions = Array.isArray(diversion.revision_history) ? diversion.revision_history : [];
  return <article className="trajectory-diversion-card">
    <header><div><span className="eyebrow">{readString(diversion, "diversion_id") ?? "Diversion ID not supplied"}</span><h3>{readString(diversion, "diversion_concept_id") ?? "Concept not supplied"}</h3>{activeForSelectedTrajectory && <span className="trajectory-active-reference-label">Referenced by the selected trajectory</span>}</div><StatusBadge tone={readString(diversion, "diversion_status") === "ACTIVE" ? "teal" : "amber"}>{readableStatus(readString(diversion, "diversion_status"))}</StatusBadge></header>
    <p>{readString(diversion, "diversion_reason") ?? "No diversion rationale supplied."}</p>
    <dl className="trajectory-context-grid"><ContextValue label="Parent trajectory" value={readString(diversion, "parent_trajectory_id") ?? "Not supplied"}/><ContextValue label="Parent concept" value={readString(diversion, "parent_concept_id") ?? "Not supplied"}/><ContextValue label="Context snapshot ID" value={readString(diversion, "context_snapshot_id") ?? "Not supplied"}/><ContextValue label="Previous learning step" value={readString(diversion, "previous_learning_step") ?? "Not supplied"}/><ContextValue label="Resumption condition" value={readString(diversion, "resume_condition") ?? "Not supplied"}/><ContextValue label="Resolution" value={readString(diversion, "resolved_at") ?? readString(diversion, "closure_reason") ?? "No resolution is recorded"}/></dl>
    <div className="diversion-support-summary"><span>{formatCount(evidenceIds.length)} supporting evidence references</span><span>{formatCount(progress.length)} progress evaluations</span><span>{formatCount(revisions.length)} saved revisions</span></div>
    {evidenceIds.length > 0 && <small>Evidence IDs: {evidenceIds.join(", ")}</small>}
    <p className="diversion-readonly-note">Resumption conditions are saved review criteria. No resumption assessment or trajectory action was submitted.</p>
  </article>;
}
