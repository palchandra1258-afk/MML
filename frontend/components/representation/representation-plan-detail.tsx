"use client";

import Link from "next/link";
import { useCallback, useMemo, type ReactNode } from "react";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { useApiResource } from "@/hooks/use-api-resource";
import type { ApiResult, BehavioralStateRecord, CognitiveStateRecord, EvidenceRecord, JsonObject, JsonValue, LearnerDetail, RepresentationRecord } from "@/lib/api/types";
import { safeErrorMessage } from "@/lib/api/errors";
import { formatCount, formatPercentage, readNumber, readObject, readString, readStringList, readableStatus } from "@/lib/learner/presentation";
import { cognitiveStateService } from "@/lib/services/cognitive-state.service";
import { evidenceService } from "@/lib/services/evidence.service";
import { learnerStateService } from "@/lib/services/learner-state.service";
import { representationService } from "@/lib/services/representation.service";

const MAX_EVIDENCE_LOOKUPS = 12;

type EvidenceLookup = { evidenceId: string; record?: EvidenceRecord; error?: unknown; requestId: string | null };
type EvidenceReference = { evidenceId: string; role: "Supporting" | "Contradictory" };

export function RepresentationPlanDetail({ learner, summaryPlan }: { learner: LearnerDetail; summaryPlan: RepresentationRecord }) {
  const loadPlan = useCallback((signal: AbortSignal) => representationService.get(learner.learner_id, summaryPlan.plan_id, signal), [learner.learner_id, summaryPlan.plan_id]);
  const detail = useApiResource<RepresentationRecord>(`${learner.learner_id}:plan:${summaryPlan.plan_id}`, loadPlan);
  return <ApiResourcePanel resource={detail.resource} retry={detail.retry} loadingLabel="Loading full representation plan" emptyTitle="Plan details unavailable" emptyMessage="The saved plan record could not be loaded.">
    {(plan, requestId) => <ApiDataBoundary requestId={requestId}><RepresentationPlanRecord learner={learner} plan={plan}/></ApiDataBoundary>}
  </ApiResourcePanel>;
}

function RepresentationPlanRecord({ learner, plan }: { learner: LearnerDetail; plan: RepresentationRecord }) {
  const input = plan.input_references;
  const behavioralReference = readObject(input.behavioral_state_reference);
  const behavioralTimestamp = readString(behavioralReference, "state_timestamp");
  const cognitiveId = readString(input, "cognitive_state_id");
  const cognitiveVersion = readNumber(input, "cognitive_state_version");
  const stateKey = learner.available_data.includes("phase9_states") && behavioralTimestamp ? `${learner.learner_id}:phase9:${behavioralTimestamp}` : null;
  const cognitiveKey = learner.available_data.includes("phase11_states") && cognitiveId ? `${learner.learner_id}:phase11:${cognitiveId}:${cognitiveVersion ?? "unknown"}` : null;
  const loadBehavioral = useCallback((signal: AbortSignal) => learnerStateService.get(learner.learner_id, signal), [learner.learner_id]);
  const loadCognitive = useCallback((signal: AbortSignal) => cognitiveStateService.getLatest(learner.learner_id, signal), [learner.learner_id]);
  const behavioral = useApiResource<BehavioralStateRecord>(stateKey, loadBehavioral);
  const cognitive = useApiResource<CognitiveStateRecord>(cognitiveKey, loadCognitive);

  const references = useMemo(() => evidenceReferences(input), [input]);
  const lookupReferences = useMemo(() => references.slice(0, MAX_EVIDENCE_LOOKUPS), [references]);
  const lookupKey = lookupReferences.map((reference) => reference.evidenceId).join("|");
  const loadEvidence = useCallback(async (signal: AbortSignal): Promise<ApiResult<EvidenceLookup[]>> => {
    const lookups = await Promise.all(lookupReferences.map(async ({ evidenceId }): Promise<EvidenceLookup> => {
      try {
        const response = await evidenceService.get(learner.learner_id, evidenceId, signal);
        return { evidenceId, record: response.data, requestId: response.requestId };
      } catch (error: unknown) {
        return { evidenceId, error, requestId: null };
      }
    }));
    return { data: lookups, requestId: null, status: 200 };
  }, [learner.learner_id, lookupReferences]);
  const evidence = useApiResource<EvidenceLookup[]>(lookupKey ? `${learner.learner_id}:plan-evidence:${plan.plan_id}:${lookupKey}` : null, loadEvidence);

  return <article className="representation-plan-record">
    <header className="representation-detail-header"><div><p className="eyebrow">PLAN DETAIL · {plan.plan_kind}</p><h3>{plan.concept_id}</h3><code>{plan.plan_id}</code></div><div className="representation-detail-status"><StatusBadge tone={plan.decision.selected_representation ? "teal" : "amber"}>{plan.decision.selected_representation ? "Recommended" : readableStatus(plan.decision.selected_action)}</StatusBadge><StatusBadge tone="neutral">Planned · execution not established</StatusBadge></div></header>
    <PlanIdentity plan={plan}/>

    <section className="representation-decision-path" aria-labelledby="representation-path-heading">
      <SectionHeading eyebrow="DECISION PATH" title="Evidence to representation decision" detail="These are saved references and rule outputs, not a validated causal chain."/>
      <ol id="representation-path-heading" className="decision-path-list">
        <li><span className="decision-path-index">01</span><div><strong>Evidence references</strong><span>{formatCount(references.length)} supporting/contradictory references in this plan</span><small>{references.length ? "Source records are looked up below." : "No evidence IDs are attached to this plan."}</small></div></li>
        <li><span className="decision-path-index">02</span><div><strong>Behavioral state</strong><span>{behavioralTimestamp ?? "Reference unavailable"}</span><small>Phase 9 response snapshot; association is checked against the saved timestamp.</small></div></li>
        <li><span className="decision-path-index">03</span><div><strong>Provisional cognitive estimate</strong><span>{cognitiveId ? `${cognitiveId}${cognitiveVersion !== undefined ? ` · v${cognitiveVersion}` : ""}` : "No cognitive-state reference"}</span><small>Phase 11 endpoint returns its latest record only.</small></div></li>
        <li><span className="decision-path-index">04</span><div><strong>Representation decision</strong><span>{plan.decision.selected_representation ?? "No representation selected"} · {plan.decision.selected_action}</span><small>{plan.decision.decision_method} · support {plan.decision.decision_confidence}</small></div></li>
        <li><span className="decision-path-index">05</span><div><strong>Capability and execution</strong><span>{plan.decision.capability_reference ? readableStatus(readString(plan.decision.capability_reference, "status")) : "No selected capability reference"}</span><small>Plan records do not contain an execution receipt.</small></div></li>
      </ol>
    </section>

    <section className="representation-explanation-section">
      <SectionHeading eyebrow="DECISION EXPLANATION" title="Why the planner chose this outcome" detail="The rationale and policy trace below are saved in this plan."/>
      <div className="decision-rationale"><StatusBadge tone="purple">{plan.decision.decision_method}</StatusBadge><p>{plan.decision.decision_reason}</p><div><span>Selected action <code>{plan.decision.selected_action}</code></span><span>Delivery status <code>{plan.decision.delivery_status}</code></span><span>Confidence scope <code>{plan.decision.confidence_scope}</code></span></div></div>
      <PolicyTrace rules={plan.decision.policy_trace}/>
    </section>

    <section className="representation-context-section">
      <SectionHeading eyebrow="SOURCE SNAPSHOTS" title="Associated behavioral and cognitive records" detail="Only the latest snapshot endpoints are available. A mismatched current snapshot is not treated as the plan's source record."/>
      <div className="representation-source-snapshots">
        <SnapshotPanel title="Behavioral state reference">
          <ApiResourcePanel resource={behavioral.resource} retry={behavioral.retry} loadingLabel="Loading behavioral snapshot" emptyTitle="Behavioral snapshot unavailable" emptyMessage="The referenced artifact is missing, not indexed, or unavailable for this learner.">
            {(record, requestId) => <ApiDataBoundary requestId={requestId}><BehavioralReference record={record} expectedTimestamp={behavioralTimestamp}/></ApiDataBoundary>}
          </ApiResourcePanel>
        </SnapshotPanel>
        <SnapshotPanel title="Cognitive-state reference">
          <ApiResourcePanel resource={cognitive.resource} retry={cognitive.retry} loadingLabel="Loading latest cognitive snapshot" emptyTitle="Cognitive snapshot unavailable" emptyMessage="The plan has no cognitive-state reference, or Phase 11 data is unavailable for this learner.">
            {(record, requestId) => <ApiDataBoundary requestId={requestId}><CognitiveReference record={record} expectedId={cognitiveId} expectedVersion={cognitiveVersion} conceptId={plan.concept_id}/></ApiDataBoundary>}
          </ApiResourcePanel>
        </SnapshotPanel>
      </div>
    </section>

    <section className="representation-evidence-section">
      <SectionHeading eyebrow="TRACEABLE INPUTS" title="Supporting and contradictory evidence" detail="Evidence IDs come from the plan inputs. Source content is not inferred when an evidence lookup fails."/>
      <div className="evidence-reference-navigation"><Link href="/progress" className="text-link">Open learner evidence and concept view</Link><Link href="/evidence" className="text-link">Open evidence explorer</Link><span>Selected research record: {learner.learner_id}</span></div>
      {references.length === 0 && <EmptyState title="No evidence references">This plan has no supporting or contradictory evidence IDs in `input_references`.</EmptyState>}
      {references.length > MAX_EVIDENCE_LOOKUPS && <p className="evidence-lookup-limit">Looking up {MAX_EVIDENCE_LOOKUPS} of {references.length} references to limit requests. All IDs remain listed in the plan fields below.</p>}
      <ApiResourcePanel resource={evidence.resource} retry={evidence.retry} loadingLabel="Loading referenced evidence records" emptyTitle="No referenced evidence" emptyMessage="No evidence IDs were attached to this plan.">
        {(lookups) => <EvidenceLookupList references={references} lookups={lookups}/>}
      </ApiResourcePanel>
    </section>

    <section className="representation-alternatives-section">
      <SectionHeading eyebrow="CAPABILITY TRACE" title="Selected capability and alternatives" detail="Availability below is the state saved with this plan, not a current registry query."/>
      {plan.decision.capability_reference ? <CapabilityReference capability={plan.decision.capability_reference}/> : <EmptyState title="No capability selected">The saved plan has no `capability_reference`; no representation is claimed as executable.</EmptyState>}
      {plan.decision.alternative_representations.length === 0 ? <EmptyState title="No alternatives recorded">No alternative representation records were returned with this plan.</EmptyState> : <div className="representation-alternative-list">{plan.decision.alternative_representations.map((alternative, index) => <article className="representation-alternative" key={`${readString(alternative, "representation_id") ?? "alternative"}-${index}`}><div><strong>{readString(alternative, "representation_id") ?? "Representation ID not supplied"}</strong><span>Saved availability <code>{readString(alternative, "availability_status") ?? "unknown"}</code> · selection <code>{readString(alternative, "selection_status") ?? "unknown"}</code></span><p>{readString(alternative, "reason") ?? "No alternative reason was supplied."}</p></div><CapabilityBadge status={readString(alternative, "availability_status")}/></article>)}</div>}
    </section>

    <section className="representation-plan-fields-section">
      <SectionHeading eyebrow="PLAN RECORD" title="Grounding, configuration, and limitations" detail="Values are rendered from fields in the saved RepresentationRecord."/>
      <PlanFields plan={plan}/>
    </section>

    <section className="representation-validation-note"><StatusBadge tone="neutral">Validation result not exposed</StatusBadge><p>The GET response has no validation outcome field, and the API has no plan-validation endpoint. A persisted plan is not presented as a separately verified validation result.</p></section>
    <nav className="representation-related-links" aria-label="Related learner views"><Link href="/learner-state">Behavioral state</Link><Link href="/cognitive-state">Cognitive state</Link><Link href="/progress">Evidence and concepts</Link><Link href="/trajectory">Learning trajectory</Link></nav>
  </article>;
}

function PlanIdentity({ plan }: { plan: RepresentationRecord }) {
  const refs = plan.input_references;
  return <dl className="representation-plan-identity-grid">
    <Definition label="Learner ID" value={plan.learner_id}/><Definition label="Plan version" value={`${plan.plan_version} · ${plan.schema_version}`}/>
    <Definition label="Taxonomy version" value={plan.taxonomy_version}/><Definition label="Created at" value={plan.created_at}/>
    <Definition label="Previous plan" value={plan.previous_plan_id ?? "None"}/><Definition label="Cognitive state" value={`${readString(refs, "cognitive_state_id") ?? "Not referenced"}${readNumber(refs, "cognitive_state_version") !== undefined ? ` · v${readNumber(refs, "cognitive_state_version")}` : ""}`}/>
    <Definition label="Supporting evidence IDs" value={readStringList(refs, "supporting_evidence_ids").join(", ") || "None"}/><Definition label="Contradictory evidence IDs" value={readStringList(refs, "contradictory_evidence_ids").join(", ") || "None"}/>
    <Definition label="Diagnostic recommendation IDs" value={readStringList(refs, "diagnostic_recommendation_ids").join(", ") || "None"}/>
  </dl>;
}

function BehavioralReference({ record, expectedTimestamp }: { record: BehavioralStateRecord; expectedTimestamp?: string }) {
  const matched = Boolean(expectedTimestamp && record.state_timestamp === expectedTimestamp);
  if (!matched) return <div className="snapshot-mismatch"><StatusBadge tone="amber">Reference mismatch</StatusBadge><p>Latest state timestamp: {record.state_timestamp ?? "Not reported"}</p><p>Plan reference timestamp: {expectedTimestamp ?? "Not supplied"}</p><small>The API returns the latest behavioral state only. This snapshot is not attributed to the plan.</small></div>;
  const performance = record.learning_performance;
  return <div className="snapshot-match"><StatusBadge tone="teal">Reference matches</StatusBadge><div className="snapshot-metrics"><span>{formatCount(readNumber(record.observation_summary, "labelled_responses"))} labeled responses</span><span>{formatPercentage(readNumber(performance, "historical_performance"))} historical correctness</span><span>{readableStatus(readString(performance, "evidence_sufficiency"))} sufficiency</span><span>{readableStatus(readString(performance, "uncertainty_level"))} uncertainty</span></div><p>Observed behavior summary, not validated cognition.</p></div>;
}

function CognitiveReference({ record, expectedId, expectedVersion, conceptId }: { record: CognitiveStateRecord; expectedId?: string; expectedVersion?: number; conceptId: string }) {
  const matched = Boolean(expectedId && record.cognitive_state_id === expectedId && (expectedVersion === undefined || record.state_version === expectedVersion));
  if (!matched) return <div className="snapshot-mismatch"><StatusBadge tone="amber">Reference mismatch</StatusBadge><p>Latest snapshot: {record.cognitive_state_id} · v{record.state_version}</p><p>Plan reference: {expectedId ?? "Not supplied"}{expectedVersion !== undefined ? ` · v${expectedVersion}` : ""}</p><small>The API has no cognitive-state-by-ID/version route. The latest snapshot is not substituted for an older reference.</small></div>;
  const estimate = record.concept_estimates.find((item) => item.concept_id === conceptId);
  return <div className="snapshot-match"><StatusBadge tone="purple">Provisional reference matches</StatusBadge><div className="snapshot-metrics"><span>Snapshot {record.cognitive_state_id} · v{record.state_version}</span><span>Overall uncertainty: {readableStatus(record.uncertainty.overall_uncertainty)}</span><span>{formatCount(record.evidence_references.length)} evidence references</span><span>{formatCount(readNumber(record.observed_evidence_summary, "contradictory_evidence_count"))} contradictory records</span></div>{estimate && <p>{readString(estimate, "concept_id")}: {readableStatus(readString(estimate, "estimated_learning_status"))}, {readableStatus(readString(estimate, "estimate_confidence"))} support. Confidence scope: {readString(estimate, "confidence_scope") ?? "Not supplied"}.</p>}<Link href="/cognitive-state" className="text-link">Open cognitive-state view</Link></div>;
}

function PolicyTrace({ rules }: { rules: JsonObject[] }) {
  if (!rules.length) return <EmptyState title="No policy trace returned">The saved plan has no `policy_trace` entries.</EmptyState>;
  return <ol className="policy-trace-list">{rules.map((rule, index) => <li key={`${readString(rule, "rule_id") ?? "rule"}-${index}`}><span className="policy-trace-number">{String(index + 1).padStart(2, "0")}</span><div className="policy-trace-content"><div><strong>{readString(rule, "rule_id") ?? "Rule ID not supplied"}</strong><small>Evidence IDs: {readStringList(rule, "evidence_ids").join(", ") || "None"}</small></div><p>{readString(rule, "explanation") ?? "No explanation supplied."}</p><div className="policy-condition-columns"><ConditionList title="Conditions satisfied" values={readStringList(rule, "conditions_satisfied")}/><ConditionList title="Conditions not satisfied" values={readStringList(rule, "conditions_not_satisfied")}/></div></div></li>)}</ol>;
}

function ConditionList({ title, values }: { title: string; values: string[] }) {
  return <div className="policy-condition-list"><strong>{title}</strong>{values.length ? <ul>{values.map((value, index) => <li key={`${value}-${index}`}>{value}</li>)}</ul> : <p>None reported.</p>}</div>;
}

function EvidenceLookupList({ references, lookups }: { references: EvidenceReference[]; lookups: EvidenceLookup[] }) {
  const lookupById = new Map(lookups.map((lookup) => [lookup.evidenceId, lookup]));
  return <div className="plan-evidence-list">{references.map((reference) => {
    const lookup = lookupById.get(reference.evidenceId);
    return <EvidenceReferenceRow key={`${reference.role}-${reference.evidenceId}`} reference={reference} lookup={lookup}/>;
  })}</div>;
}

function EvidenceReferenceRow({ reference, lookup }: { reference: EvidenceReference; lookup?: EvidenceLookup }) {
  if (!lookup) return <article className="plan-evidence-row"><StatusBadge tone="neutral">{reference.role}</StatusBadge><div><strong>{reference.evidenceId}</strong><p>This reference is outside the current lookup limit.</p></div></article>;
  if (lookup.error) return <article className="plan-evidence-row"><StatusBadge tone="amber">{reference.role} · unresolved</StatusBadge><div><strong>{reference.evidenceId}</strong><p>{safeErrorMessage(lookup.error)}</p>{lookup.requestId && <small>Request {lookup.requestId}</small>}</div></article>;
  const record = lookup.record;
  if (!record) return <article className="plan-evidence-row"><StatusBadge tone="amber">{reference.role} · unavailable</StatusBadge><div><strong>{reference.evidenceId}</strong><p>The evidence endpoint returned no record.</p></div></article>;
  return <article className="plan-evidence-row"><StatusBadge tone={reference.role === "Supporting" ? "teal" : "amber"}>{reference.role}</StatusBadge><div><strong>{record.evidence_id}</strong><span>{record.evidence_type} · {record.provenance.source_dataset} · {record.provenance.source_modality}</span><small>Source record {record.provenance.source_record_id ?? "not supplied"} · sequence {record.temporal.sequence_number ?? "not supplied"}</small><small>Timestamp meaning: {record.temporal.timestamp_source ?? "not supplied"} · processing {record.processing.status}</small>{(record.uncertainty.flags.length > 0 || record.uncertainty.notes.length > 0) && <p>{[...record.uncertainty.flags, ...record.uncertainty.notes].join(" · ")}</p>}</div><span className="evidence-request-id">{lookup.requestId ? `Request ${lookup.requestId}` : ""}</span></article>;
}

function CapabilityReference({ capability }: { capability: JsonObject }) {
  return <div className="selected-capability-reference"><CapabilityBadge status={readString(capability, "status")}/><dl className="representation-plan-identity-grid"><Definition label="Representation ID" value={readString(capability, "representation_id") ?? "Not supplied"}/><Definition label="Provider ID" value={readString(capability, "provider_id") ?? "None"}/><Definition label="Content IDs" value={readStringList(capability, "content_ids").join(", ") || "None"}/><Definition label="Reason" value={readString(capability, "reason") ?? "Not supplied"}/></dl><p>A capability reference in a plan is not a delivery receipt.</p></div>;
}

function CapabilityBadge({ status }: { status?: string }) {
  const label = status === "available" ? "Available in saved plan" : status === "planned" ? "Not configured in saved plan" : status === "unavailable" ? "Unavailable in saved plan" : "Unknown saved status";
  return <StatusBadge tone={status === "available" ? "teal" : status === "unavailable" ? "amber" : "neutral"}>{label}</StatusBadge>;
}

function PlanFields({ plan }: { plan: RepresentationRecord }) {
  const objective = plan.learning_objective;
  const objectiveText = readString(objective, "objective_text");
  const grounding = plan.concept_grounding;
  return <div className="representation-plan-fields">
    <dl className="representation-plan-identity-grid"><Definition label="Objective status" value={readString(objective, "objective_status") ?? "Not reported"}/><Definition label="Objective text" value={objectiveText ?? "Unavailable"}/><Definition label="Intended outcome" value={readString(objective, "intended_learning_outcome") ?? "Not supplied"}/><Definition label="Concept name status" value={readString(grounding, "name_status") ?? "Not supplied"}/><Definition label="Source dataset" value={readString(grounding, "source_dataset") ?? "Not supplied"}/><Definition label="Content status" value={readString(grounding, "content_status") ?? "Not reported"}/><Definition label="Related question IDs" value={`${formatCount(readNumber(grounding, "related_question_id_count"))}${grounding.related_question_ids_truncated === true ? " · truncated" : ""}`}/><Definition label="Related lecture IDs" value={formatCount(readNumber(grounding, "related_lecture_id_count"))}/><Definition label="Representation configuration" value={formatObject(plan.representation_configuration)}/></dl>
    {plan.evaluation_strategy.length > 0 && <div className="plan-strategy-list"><h4>Saved evaluation strategy</h4>{plan.evaluation_strategy.map((item, index) => <article key={`${readString(item, "method") ?? "strategy"}-${index}`}><strong>{readableStatus(readString(item, "method"))}</strong><p>{readString(item, "purpose") ?? "Purpose not supplied."}</p><small>{readString(item, "success_measure") ?? "No success measure supplied."} · {readableStatus(readString(item, "status"))}</small></article>)}</div>}
    {Object.entries(plan.limitations).map(([category, values]) => <div className="plan-limitation-group" key={category}><strong>{readableStatus(category)}</strong><ul>{stringValues(values).map((value, index) => <li key={`${value}-${index}`}>{value}</li>)}</ul></div>)}
  </div>;
}

function formatObject(object: JsonObject): string {
  const entries = Object.entries(object);
  return entries.length ? entries.map(([key, value]) => `${key}: ${formatJsonValue(value)}`).join(" · ") : "No configuration fields";
}

function formatJsonValue(value: JsonValue): string {
  if (value === null) return "null";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map(formatJsonValue).join(", ");
  return Object.entries(value).map(([key, child]) => `${key}=${formatJsonValue(child)}`).join(", ");
}

function stringValues(value: JsonValue | undefined): string[] {
  if (typeof value === "string") return [value];
  return Array.isArray(value) ? value.flatMap(stringValues) : [];
}

function evidenceReferences(input: JsonObject): EvidenceReference[] {
  const roles = new Map<string, Set<EvidenceReference["role"]>>();
  for (const id of readStringList(input, "supporting_evidence_ids")) {
    const current = roles.get(id) ?? new Set<EvidenceReference["role"]>();
    current.add("Supporting");
    roles.set(id, current);
  }
  for (const id of readStringList(input, "contradictory_evidence_ids")) {
    const current = roles.get(id) ?? new Set<EvidenceReference["role"]>();
    current.add("Contradictory");
    roles.set(id, current);
  }
  return [...roles.entries()].flatMap(([evidenceId, evidenceRoles]) => [...evidenceRoles].map((role) => ({ evidenceId, role })));
}

function SnapshotPanel({ title, children }: { title: string; children: ReactNode }) {
  return <section className="representation-snapshot-panel"><h3>{title}</h3>{children}</section>;
}

function Definition({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
