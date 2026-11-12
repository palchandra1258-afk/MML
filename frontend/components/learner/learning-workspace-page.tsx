"use client";

import { useCallback } from "react";
import Link from "next/link";
import { EmptyState } from "@/components/shared/data-states";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { LearnerPageHeading, ResearchDataNotice, SelectedLearnerSummary, SelectedRecordRequired } from "@/components/learner/learner-page-common";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import type { ApiPage, LearnerDetail, RepresentationRecord, TrajectoryRecord } from "@/lib/api/types";
import { representationService } from "@/lib/services/representation.service";
import { trajectoryService } from "@/lib/services/trajectory.service";
import { loadLatestIndexedPage } from "@/lib/learner/data";
import { artifactResourceKey, formatCount, readNumber, readString, readStringList, readableStatus } from "@/lib/learner/presentation";

export function LearningWorkspacePage() {
  const { learner } = useLearnerSelection();
  if (!learner) return <SelectedRecordRequired/>;
  return <LearningWorkspaceForLearner key={learner.learner_id} learnerId={learner.learner_id} availableData={learner.available_data} trajectoryCount={learner.trajectory_count} learner={learner}/>;
}

function LearningWorkspaceForLearner({ learnerId, availableData, trajectoryCount, learner }: { learnerId: string; availableData: string[]; trajectoryCount: number; learner: LearnerDetail }) {
  const loadPlans = useCallback((signal: AbortSignal) => loadLatestIndexedPage(
    (query) => representationService.list(learnerId, query), 5, signal,
  ), [learnerId]);
  const loadTrajectories = useCallback((signal: AbortSignal) => trajectoryService.list(learnerId, { limit: 5, offset: 0, signal }), [learnerId]);
  const plans = useApiResource<ApiPage<RepresentationRecord>>(
    artifactResourceKey(learnerId, availableData, "phase12_plans"),
    loadPlans,
  );
  const trajectories = useApiResource<ApiPage<TrajectoryRecord>>(
    trajectoryCount > 0 ? `${learnerId}:trajectories` : null,
    loadTrajectories,
  );

  return <div className="learner-experience-page">
    <LearnerPageHeading eyebrow="LEARNING STUDIO" title="Learning workspace" description="Review the saved learning context available for this record. No content is generated or delivered here."/>
    <SelectedLearnerSummary learner={learner}/>
    <section className="learning-activity-unavailable"><span className="research-data-notice-icon" aria-hidden="true">i</span><div><strong>No learning activity can be opened</strong><p>The API has no lesson-content, quiz, answer-submission, feedback, or adaptive-content endpoint. A recommendation cannot be treated as delivered instruction.</p></div><StatusBadge tone="amber">Content provider unavailable</StatusBadge></section>

    <div className="learning-workspace-grid">
      <section className="panel learner-overview-panel">
        <SectionHeading eyebrow="SAVED REPRESENTATION PLAN" title="Available learning context" detail="A plan describes a recommendation and its evidence; it does not contain executable lesson content."/>
        <ApiResourcePanel resource={plans.resource} retry={plans.retry} loadingLabel="Loading saved plans" emptyTitle="No saved plan available" emptyMessage="This record has no Phase 12 plan. No goal or activity is inferred from its response history.">
          {(page, requestId) => <ApiDataBoundary requestId={requestId}><PlanContext page={page}/></ApiDataBoundary>}
        </ApiResourcePanel>
      </section>
      <section className="panel learner-overview-panel">
        <SectionHeading eyebrow="SAVED TRAJECTORY INDEX" title="Persisted path context" detail="Returned trajectory snapshots are system records, not evidence that an activity was completed."/>
        <ApiResourcePanel resource={trajectories.resource} retry={trajectories.retry} loadingLabel="Loading trajectory context" emptyTitle="No current trajectory" emptyMessage="No persisted trajectory is available for this learner record.">
          {(page, requestId) => <ApiDataBoundary requestId={requestId}><WorkspaceTrajectory page={page}/></ApiDataBoundary>}
        </ApiResourcePanel>
      </section>
    </div>

    <section className="panel learning-next-actions">
      <SectionHeading eyebrow="AVAILABLE TODAY" title="Inspect the evidence behind the record" detail="These links open saved research data and do not start an activity."/>
      <div className="learner-workspace-links"><Link href="/progress" className="placeholder-link panel"><span>Review response history</span><span aria-hidden="true">→</span></Link><Link href="/cognitive-state" className="placeholder-link panel"><span>Inspect provisional estimate</span><span aria-hidden="true">→</span></Link><Link href="/trajectory" className="placeholder-link panel"><span>Review trajectory and history</span><span aria-hidden="true">→</span></Link></div>
    </section>
    <ResearchDataNotice>EdNet skill IDs are dataset tags with no validated curriculum or prerequisite graph. No lesson objective is shown unless an API record supplies one.</ResearchDataNotice>
  </div>;
}

function PlanContext({ page }: { page: ApiPage<RepresentationRecord> }) {
  if (!page.items.length) return <EmptyState title="No representation plans returned">The API returned an empty plan page.</EmptyState>;
  const plan = page.items[page.items.length - 1];
  const objectiveText = readString(plan.learning_objective, "objective_text");
  const objectiveOutcome = readString(plan.learning_objective, "intended_learning_outcome");
  const supportingEvidenceIds = readStringList(plan.input_references, "supporting_evidence_ids");
  const contradictoryEvidenceIds = readStringList(plan.input_references, "contradictory_evidence_ids");
  const recommendationIds = readStringList(plan.input_references, "diagnostic_recommendation_ids");
  return <div className="workspace-plan-context"><div className="workspace-plan-identity"><div><span className="eyebrow">{plan.plan_kind} · version {plan.plan_version}</span><strong>{plan.concept_id}</strong><span>Plan ID {plan.plan_id}</span></div><StatusBadge tone={plan.decision.delivery_status === "delivered" ? "teal" : "amber"}>{readableStatus(plan.decision.delivery_status)}</StatusBadge></div>
    <dl className="workspace-plan-fields"><div><dt>Objective text</dt><dd>{objectiveText ?? "No learner-facing objective supplied"}</dd></div><div><dt>Objective status</dt><dd>{readableStatus(readString(plan.learning_objective, "objective_status"))}</dd></div><div><dt>Plan action</dt><dd>{readableStatus(plan.decision.selected_action)}</dd></div><div><dt>Selected representation</dt><dd>{plan.decision.selected_representation ?? "None selected"}</dd></div><div><dt>Capability reference</dt><dd>{plan.decision.capability_reference ? "A capability reference is present; no execution route exists." : "None returned"}</dd></div><div><dt>Cognitive state reference</dt><dd>{readString(plan.input_references, "cognitive_state_id") ?? "None returned"}</dd></div><div><dt>Source dataset</dt><dd>{readString(plan.concept_grounding, "source_dataset") ?? "Not supplied"}</dd></div><div><dt>Concept name status</dt><dd>{readableStatus(readString(plan.concept_grounding, "name_status"))}</dd></div><div><dt>Related question references</dt><dd>{formatCount(readNumber(plan.concept_grounding, "related_question_id_count"))} identifiers · {readableStatus(readString(plan.concept_grounding, "content_status"))}</dd></div></dl>
    <div className="workspace-evidence-references"><strong>Evidence and recommendation references</strong><span>Supporting: {supportingEvidenceIds.join(", ") || "None returned"}</span><span>Contradictory: {contradictoryEvidenceIds.join(", ") || "None returned"}</span><span>Diagnostic recommendations: {recommendationIds.join(", ") || "None returned"}</span></div>
    {objectiveOutcome && <p className="workspace-outcome-note"><strong>Recorded intended outcome:</strong> {objectiveOutcome}</p>}
    <div className="workspace-plan-reason"><span>Decision rationale</span><p>{plan.decision.decision_reason}</p></div>
    <div className="workspace-plan-limitations"><strong>Plan limitations</strong><p>{Object.values(plan.limitations).filter((value): value is string => typeof value === "string").join(" · ") || "No plain-text limitation fields were supplied."}</p></div>
    <p className="workspace-plan-note">Saved plan only · recommendation does not mean content was delivered or learning improved.</p>
  </div>;
}

function WorkspaceTrajectory({ page }: { page: ApiPage<TrajectoryRecord> }) {
  if (!page.items.length) return <EmptyState title="No persisted trajectory">The API returned an empty trajectory index.</EmptyState>;
  return <div className="workspace-trajectory-context"><p className="trajectory-page-note">Showing {page.items.length} of {page.total} saved trajectory records from the returned index page.</p>{page.items.map((trajectory) => <article className="workspace-trajectory-record" key={trajectory.trajectory_id}><StatusBadge tone={trajectory.current_status === "ACTIVE" ? "teal" : "amber"}>{readableStatus(trajectory.current_status)}</StatusBadge><h3>{trajectory.primary_learning_goal}</h3><p>Current recorded step: {trajectory.current_learning_step || "Not supplied"}</p><span>{trajectory.completed_steps.length} completed-step records · {trajectory.pending_steps.length} pending-step records</span><small>{trajectory.trajectory_id} · version {trajectory.trajectory_version} · updated {trajectory.updated_at}</small></article>)}</div>;
}
