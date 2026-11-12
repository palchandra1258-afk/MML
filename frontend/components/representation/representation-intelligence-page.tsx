"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { ResearchDataNotice, SelectedLearnerSummary } from "@/components/learner/learner-page-common";
import { DataSourceLabel, EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiHealth } from "@/hooks/use-api-health";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import type { ApiPage, HealthData, RepresentationRecord } from "@/lib/api/types";
import { formatCount, readNumber, readString, readStringList, readableStatus } from "@/lib/learner/presentation";
import { defaultCapabilityRegistry, representationTaxonomy, taxonomyVersion, type RepresentationDefinition } from "@/lib/representation/catalog";
import { filterPlanRecords, savedCapabilityObservations, selectPlanFromPage, summarizePlanRecords, type PlanFilter, type PlanSearchFilters } from "@/lib/representation/plan-analysis";
import { representationService } from "@/lib/services/representation.service";
import { RepresentationPlanDetail } from "@/components/representation/representation-plan-detail";

const PAGE_SIZE = 25;
const EMPTY_FILTERS: PlanSearchFilters = { category: "all", planStatus: "all", query: "", selectedRepresentation: "all", capabilityStatus: "all", version: "all", dateFrom: "", dateTo: "" };

export function RepresentationIntelligencePage() {
  const { learner } = useLearnerSelection();
  const { state: connection, health } = useApiHealth();
  const [selectedRepresentationId, setSelectedRepresentationId] = useState<string>(representationTaxonomy[0]?.representation_id ?? "");
  const [planOffset, setPlanOffset] = useState(0);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [planFilters, setPlanFilters] = useState<PlanSearchFilters>(EMPTY_FILTERS);
  const [comparePlanIds, setComparePlanIds] = useState<string[]>([]);
  const learnerId = learner?.learner_id ?? "";
  const canReadPlans = Boolean(learner && learner.available_data.includes("phase12_plans") && connection === "connected");
  const planKey = canReadPlans ? `${learnerId}:phase12:${planOffset}` : null;

  const loadPlans = useCallback((signal: AbortSignal) => representationService.list(learnerId, { limit: PAGE_SIZE, offset: planOffset, signal }), [learnerId, planOffset]);
  const plans = useApiResource<ApiPage<RepresentationRecord>>(planKey, loadPlans);
  const planPage = plans.resource.status === "success" ? plans.resource.data : undefined;
  const visiblePlans = planPage ? filterPlanRecords(planPage.items, planFilters) : [];
  const selectedPlan = selectPlanFromPage(visiblePlans, selectedPlanId);
  const summary = planPage ? summarizePlanRecords(planPage.items) : null;
  const capabilityObservations = planPage ? savedCapabilityObservations(planPage.items) : [];
  const comparisonPlans = useMemo(() => planPage?.items.filter((plan) => comparePlanIds.includes(plan.plan_id)) ?? [], [comparePlanIds, planPage]);
  const pageStatuses = [...new Set([...(planPage?.items.map((plan) => plan.decision.delivery_status) ?? []), ...(planFilters.planStatus === "all" ? [] : [planFilters.planStatus])])].sort();
  const pageRepresentations = [...new Set([...(planPage?.items.map((plan) => plan.decision.selected_representation).filter((value): value is string => Boolean(value)) ?? []), ...(planFilters.selectedRepresentation === "all" || planFilters.selectedRepresentation === "none" ? [] : [planFilters.selectedRepresentation])])].sort();
  const pageCapabilityStatuses = [...new Set([...(planPage?.items ?? []).flatMap((plan) => [plan.decision.capability_reference ? readString(plan.decision.capability_reference, "status") : undefined, ...plan.decision.alternative_representations.map((item) => readString(item, "availability_status"))]).filter((value): value is string => Boolean(value)), ...(planFilters.capabilityStatus === "all" ? [] : [planFilters.capabilityStatus])])].sort();
  const pageVersions = [...new Set([...(planPage?.items.map((plan) => String(plan.plan_version)) ?? []), ...(planFilters.version === "all" ? [] : [planFilters.version])])].sort((a, b) => Number(a) - Number(b));
  const selectedDefinition = representationTaxonomy.find((item) => item.representation_id === selectedRepresentationId) ?? representationTaxonomy[0];

  const updateFilter = <K extends keyof PlanSearchFilters>(key: K, value: PlanSearchFilters[K]) => setPlanFilters((current) => ({ ...current, [key]: value }));
  const toggleCompare = (planId: string, checked: boolean) => setComparePlanIds((current) => checked ? current.length < 2 && !current.includes(planId) ? [...current, planId] : current : current.filter((id) => id !== planId));

  const renderPlanPage = (page: ApiPage<RepresentationRecord>, requestId: string | null) => <ApiDataBoundary requestId={requestId}>
    <div className="representation-plan-summary">
      <PlanMetric label="Saved plans for this learner" value={formatCount(page.total)} detail="API total"/>
      <PlanMetric label="Selected representation" value={formatCount(summary?.selected)} detail="Retrieved page"/>
      <PlanMetric label="No representation selected" value={formatCount(summary?.noSelection)} detail="Retrieved page"/>
      <PlanMetric label="Additional evidence requested" value={formatCount(summary?.additionalEvidence)} detail="Retrieved page"/>
      <PlanMetric label="Diagnostic plan records" value={formatCount(summary?.diagnostic)} detail="Retrieved page"/>
      <PlanMetric label="Deferred for capability" value={formatCount(summary?.deferred)} detail="Retrieved page"/>
    </div>
    <p className="representation-count-scope">The API total is for this selected learner. Category counts are derived from the {page.items.length} records on page {Math.floor(page.offset / Math.max(page.limit, 1)) + 1}; categories can overlap.</p>
    <div className="representation-plan-filters" aria-label="Filter saved plans">
      <label className="representation-search-field" htmlFor="representation-plan-search">Search this page<span>Identifiers, rationale, evidence IDs, and saved fields</span><input id="representation-plan-search" type="search" value={planFilters.query} onChange={(event) => updateFilter("query", event.target.value)} placeholder="Search plans, concepts, evidence…"/></label>
      <label htmlFor="representation-plan-category">Decision category<select id="representation-plan-category" value={planFilters.category} onChange={(event) => updateFilter("category", event.target.value as PlanFilter)}><option value="all">All categories</option><option value="selected">Representation selected</option><option value="no-selection">No representation selected</option><option value="additional-evidence">Additional evidence requested</option><option value="diagnostic">Diagnostic plan</option><option value="deferred">Deferred</option></select></label>
      <label htmlFor="representation-plan-status">Saved delivery status<select id="representation-plan-status" value={planFilters.planStatus} onChange={(event) => updateFilter("planStatus", event.target.value)}><option value="all">All statuses</option>{pageStatuses.map((status) => <option value={status} key={status}>{readableStatus(status)} · {status}</option>)}</select></label>
      <label htmlFor="representation-plan-representation">Selected representation<select id="representation-plan-representation" value={planFilters.selectedRepresentation} onChange={(event) => updateFilter("selectedRepresentation", event.target.value)}><option value="all">All representations</option><option value="none">No representation selected</option>{pageRepresentations.map((representation) => <option value={representation} key={representation}>{representation}</option>)}</select></label>
      <label htmlFor="representation-plan-capability">Saved capability status<select id="representation-plan-capability" value={planFilters.capabilityStatus} onChange={(event) => updateFilter("capabilityStatus", event.target.value)}><option value="all">All saved statuses</option>{pageCapabilityStatuses.map((status) => <option value={status} key={status}>{readableStatus(status)} · {status}</option>)}</select></label>
      <label htmlFor="representation-plan-version">Plan version<select id="representation-plan-version" value={planFilters.version} onChange={(event) => updateFilter("version", event.target.value)}><option value="all">All versions</option>{pageVersions.map((version) => <option value={version} key={version}>v{version}</option>)}</select></label>
      <label htmlFor="representation-plan-from">Created from<input id="representation-plan-from" type="date" value={planFilters.dateFrom} onChange={(event) => updateFilter("dateFrom", event.target.value)}/></label>
      <label htmlFor="representation-plan-to">Created through<input id="representation-plan-to" type="date" value={planFilters.dateTo} onChange={(event) => updateFilter("dateTo", event.target.value)}/></label>
      <button className="button button--secondary representation-filter-reset" type="button" onClick={() => setPlanFilters({ ...EMPTY_FILTERS })} disabled={JSON.stringify(planFilters) === JSON.stringify(EMPTY_FILTERS)}>Reset filters</button>
    </div>
    <p className="representation-count-scope">Search and filters apply to the currently retrieved page of {page.items.length} records for learner {learnerId}. The learner selector scopes the API request; page filters do not search other learners or pages.</p>
    {page.items.length > 0 && <div className="learner-index-pagination representation-pagination"><button type="button" className="button button--secondary" disabled={page.offset === 0 || plans.resource.status === "loading"} onClick={() => { setComparePlanIds([]); setPlanOffset((current) => Math.max(0, current - PAGE_SIZE)); }}>Previous</button><span>{page.offset + 1}–{Math.min(page.offset + page.items.length, page.total)} of {page.total.toLocaleString()} plans</span><button type="button" className="button button--secondary" disabled={!page.has_more || plans.resource.status === "loading"} onClick={() => { setComparePlanIds([]); setPlanOffset((current) => current + PAGE_SIZE); }}>Next</button></div>}
    <p className="representation-comparison-instruction">Select up to two plans from this page to compare. Comparison does not rank plans or imply equivalent concepts.</p>
    <div className="representation-plan-layout">
      <div className="representation-plan-index" role="group" aria-label="Representation plan results">
        {visiblePlans.length === 0 ? <EmptyState title="No plans match these filters">There are no matching plan records on the retrieved page. Reset filters or move to another API page.</EmptyState> : visiblePlans.map((plan) => <article className="representation-plan-row-wrap" key={plan.plan_id}>
          <button type="button" className={`representation-plan-row ${selectedPlan?.plan_id === plan.plan_id ? "representation-plan-row--active" : ""}`} aria-pressed={selectedPlan?.plan_id === plan.plan_id} onClick={() => setSelectedPlanId(plan.plan_id)}>
            <span className="representation-plan-row-title"><strong>{plan.concept_id}</strong><small>{plan.plan_id}</small></span>
            <span className="representation-plan-row-tags"><StatusBadge tone={plan.decision.selected_representation ? "teal" : "amber"}>{plan.decision.selected_representation ? "Recommended" : readableStatus(plan.decision.selected_action)}</StatusBadge><StatusBadge tone="neutral">{readableStatus(plan.decision.delivery_status)} · {plan.decision.delivery_status}</StatusBadge></span>
            <span className="representation-plan-row-footer">{plan.learner_id} · {plan.plan_kind} · v{plan.plan_version} · {plan.created_at}</span>
          </button>
          <label className="representation-compare-choice"><input type="checkbox" checked={comparePlanIds.includes(plan.plan_id)} onChange={(event) => toggleCompare(plan.plan_id, event.target.checked)} disabled={!comparePlanIds.includes(plan.plan_id) && comparePlanIds.length >= 2}/><span>Compare</span></label>
        </article>)}
      </div>
      <div className="representation-plan-detail">
        {selectedPlan ? <RepresentationPlanDetail key={selectedPlan.plan_id} learner={learner!} summaryPlan={selectedPlan}/> : <EmptyState title="Select a saved plan">Choose a plan record to inspect its inputs, rule trace, capabilities, and saved outcome.</EmptyState>}
      </div>
    </div>
    <PlanComparison plans={comparisonPlans}/>
  </ApiDataBoundary>;

  return <div className="representation-intelligence-page">
    <header className="representation-page-heading"><div><p className="eyebrow">COGNITIVE INTELLIGENCE</p><h2>Representation intelligence<span className="welcome-period">.</span></h2><p>Inspect the versioned taxonomy, default repository capabilities, and saved learner-scoped plans with their decision evidence.</p></div><DataSourceLabel kind={connection === "connected" ? "api" : "unavailable"} detail={connection === "connected" ? "API connected · repository snapshot separately labeled" : "Live API unavailable · repository snapshot only"}/></header>
    <section className="representation-source-note"><span className="research-data-notice-icon" aria-hidden="true">i</span><p><strong>Separate definitions from execution.</strong> The taxonomy and default registry below are snapshots of backend source definitions. The API has no taxonomy or registry endpoint. Saved plans and health status are read from the live API when connected.</p><StatusBadge tone="amber">No activity is launched</StatusBadge></section>

    <OverviewMetrics health={health ?? null} planPage={planPage}/>
    <TaxonomyExplorer selectedId={selectedDefinition?.representation_id ?? ""} onSelect={setSelectedRepresentationId} selected={selectedDefinition}/>
    <CapabilityRegistry health={health ?? null} observations={capabilityObservations}/>

    <section className="panel representation-plans-panel">
      <SectionHeading eyebrow="SAVED REPRESENTATION PLANS" title="Plan explorer" detail="Plans are immutable saved recommendations. Select one to inspect its source references and decision trace."/>
      {!learner && <EmptyState title="Choose a research record">Select a pseudonymous learner record on the <Link href="/">overview</Link> first. The API has no global plan list.</EmptyState>}
      {learner && <SelectedLearnerSummary learner={learner}/>}
      {learner && connection === "connecting" && <EmptyState title="Connecting to the API">The plan index will load after the backend health check completes.</EmptyState>}
      {learner && (connection === "disconnected" || connection === "error" || connection === "mock") && <EmptyState title="Live representation plans are unavailable">The current mode or connection does not provide live plan records. Repository taxonomy definitions remain visible; no synthetic plan is substituted.</EmptyState>}
      {learner && connection === "connected" && !learner.available_data.includes("phase12_plans") && <EmptyState title="No representation plans are indexed for this record">The learner detail response does not list Phase 12 plans for this record.</EmptyState>}
      {learner && connection === "connected" && learner.available_data.includes("phase12_plans") && <ApiResourcePanel resource={plans.resource} retry={plans.retry} loadingLabel="Loading representation plans" emptyTitle="No saved representation plans" emptyMessage="The API returned no representation plans for this selected learner.">{renderPlanPage}</ApiResourcePanel>}
      <ResearchDataNotice>Plan categories are derived from `selected_representation`, `selected_action`, `delivery_status`, and `plan_kind`. They are not validation classes; the API exposes no plan-validation result or rejected-plan endpoint.</ResearchDataNotice>
    </section>
    <ResearchDataNotice>Repository taxonomy examples describe representation patterns, not available lesson content. A plan marked available still does not prove that content was displayed or used. No exposure receipt is part of the plan API schema.</ResearchDataNotice>
  </div>;
}

function OverviewMetrics({ health, planPage }: { health: HealthData | null; planPage: ApiPage<RepresentationRecord> | undefined }) {
  const phase12 = health?.modules.phase12_representation;
  const plansAvailable = typeof phase12?.record_count === "number" ? phase12.record_count : undefined;
  const registeredCount = defaultCapabilityRegistry.length;
  const availableCount = defaultCapabilityRegistry.filter((item) => String(item.status) === "available").length;
  const unavailableCount = defaultCapabilityRegistry.filter((item) => String(item.status) === "unavailable").length;
  const plannedCount = defaultCapabilityRegistry.filter((item) => String(item.status) === "planned").length;
  return <section className="representation-overview-metrics" aria-label="Representation system summary">
    <PlanMetric label="Taxonomy definitions" value={formatCount(representationTaxonomy.length)} detail={`Repository snapshot · v${taxonomyVersion}`}/>
    <PlanMetric label="Default registry entries" value={formatCount(registeredCount)} detail="Repository default"/>
    <PlanMetric label="Default available" value={formatCount(availableCount)} detail="Repository default"/>
    <PlanMetric label="Default unavailable" value={formatCount(unavailableCount)} detail="Repository default"/>
    <PlanMetric label="Default not configured" value={formatCount(plannedCount)} detail="Repository default"/>
    <PlanMetric label="Phase 12 plans indexed" value={health ? formatCount(plansAvailable) : "Not reported"} detail={health ? "Health endpoint total" : "API not connected"}/>
    <PlanMetric label="Selected learner plans" value={planPage ? formatCount(planPage.total) : "Select a record"} detail="Learner-scoped API total"/>
  </section>;
}

function PlanMetric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <div className="representation-overview-metric"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function PlanComparison({ plans }: { plans: RepresentationRecord[] }) {
  return <section className="representation-comparison-panel panel">
    <SectionHeading eyebrow="PLAN COMPARISON" title="Compare saved decisions" detail="Descriptive comparison of up to two records from the current API page; there is no ranking or effectiveness score."/>
    {plans.length === 0 ? <EmptyState title="Choose plans to compare">Use the Compare checkboxes beside up to two plans on this page.</EmptyState> : plans.length === 1 ? <EmptyState title="Choose one more plan">{plans[0].plan_id} is selected. Choose a second plan from the current page.</EmptyState> : <>
      <p className="representation-count-scope">The records may concern different concepts or evidence windows. Compare their saved fields as distinct decisions; this view does not establish that they are equivalent or comparable interventions.</p>
      <div className="representation-comparison-table-wrap"><table className="representation-comparison-table"><caption>Saved representation plan fields</caption><thead><tr><th scope="col">Field</th>{plans.map((plan) => <th scope="col" key={plan.plan_id}><strong>{plan.plan_id}</strong><small>{plan.concept_id} · {plan.created_at}</small></th>)}</tr></thead><tbody>
        <ComparisonRow label="Learner" values={plans.map((plan) => plan.learner_id)}/>
        <ComparisonRow label="Selected representation" values={plans.map((plan) => plan.decision.selected_representation ?? "None")}/>
        <ComparisonRow label="Plan action" values={plans.map((plan) => `${plan.decision.selected_action} · delivery ${plan.decision.delivery_status}`)}/>
        <ComparisonRow label="Supporting evidence IDs" values={plans.map((plan) => readStringList(plan.input_references, "supporting_evidence_ids").join(", ") || "None")}/>
        <ComparisonRow label="Contradictory evidence IDs" values={plans.map((plan) => readStringList(plan.input_references, "contradictory_evidence_ids").join(", ") || "None")}/>
        <ComparisonRow label="Cognitive-state reference" values={plans.map((plan) => `${readString(plan.input_references, "cognitive_state_id") ?? "None"}${readNumber(plan.input_references, "cognitive_state_version") !== undefined ? ` · v${readNumber(plan.input_references, "cognitive_state_version")}` : ""}`)}/>
        <ComparisonRow label="Capability observations" values={plans.map((plan) => capabilitySummary(plan))}/>
        <ComparisonRow label="Decision rationale" values={plans.map((plan) => `${plan.decision.decision_method}: ${plan.decision.decision_reason}`)}/>
        <ComparisonRow label="Validation outcome" values={plans.map(() => "Not exposed by the plan API")}/>
        <ComparisonRow label="Execution evidence" values={plans.map(() => "No execution receipt exposed; execution not established")}/>
      </tbody></table></div>
    </>}
  </section>;
}

function ComparisonRow({ label, values }: { label: string; values: string[] }) {
  return <tr><th scope="row">{label}</th>{values.map((value, index) => <td key={`${label}-${index}`}>{value}</td>)}</tr>;
}

function capabilitySummary(plan: RepresentationRecord): string {
  const selected = plan.decision.capability_reference;
  const selectedValue = selected ? `${readString(selected, "representation_id") ?? "selected type"}: ${readString(selected, "status") ?? "unknown"}` : "No selected capability";
  const alternatives = plan.decision.alternative_representations.map((item) => `${readString(item, "representation_id") ?? "type"}: ${readString(item, "availability_status") ?? "unknown"}`);
  return [selectedValue, ...alternatives].join("; ");
}

function TaxonomyExplorer({ selectedId, onSelect, selected }: { selectedId: string; onSelect: (id: string) => void; selected: RepresentationDefinition }) {
  const capability = defaultCapabilityRegistry.find((item) => item.representation_id === selected.representation_id);
  return <section className="panel taxonomy-explorer-panel">
    <SectionHeading eyebrow="REPRESENTATION TAXONOMY" title="Taxonomy explorer" detail={`Backend source definition snapshot · taxonomy version ${taxonomyVersion}. Select a type to inspect its registered fields.`}/>
    <div className="taxonomy-explorer-layout">
      <div className="taxonomy-type-list" role="group" aria-label="Representation types">
        {representationTaxonomy.map((item) => <button type="button" className={`taxonomy-type-button ${selectedId === item.representation_id ? "taxonomy-type-button--active" : ""}`} aria-pressed={selectedId === item.representation_id} onClick={() => onSelect(item.representation_id)} key={item.representation_id}><strong>{item.label}</strong><code>{item.representation_id}</code></button>)}
      </div>
      <article className="taxonomy-type-detail">
        <div className="taxonomy-type-heading"><div><span className="eyebrow">REPRESENTATION IDENTIFIER</span><h3>{selected.label}</h3><code>{selected.representation_id}</code></div><StatusBadge tone="neutral">Taxonomy definition</StatusBadge></div>
        <div className="taxonomy-detail-grid"><div><h4>Taxonomy examples</h4><ul>{selected.examples.map((example) => <li key={example}>{example}</li>)}</ul></div><div><h4>Configuration fields</h4><ul>{selected.configuration_fields.map((field) => <li key={field}><code>{field}</code></li>)}</ul></div><div className="taxonomy-associated-capability"><h4>Associated default capability</h4>{capability ? <><CapabilityStatus status={capability.status}/><p>{capability.reason}</p></> : <p>No matching default registry entry is present in this source snapshot.</p>}</div></div>
        <p>Examples are labels in the taxonomy source. The schema has no category, prose description, or runtime-constraint field; examples do not indicate that content or a renderer exists.</p>
      </article>
    </div>
  </section>;
}

function CapabilityRegistry({ health, observations }: { health: HealthData | null; observations: ReturnType<typeof savedCapabilityObservations> }) {
  const phase12 = health?.modules.phase12_representation;
  const deliveryProvider = phase12?.delivery_provider;
  const runtimeLabel = deliveryProvider === false ? "No delivery provider reported by API health" : deliveryProvider === true ? "Provider reported; type-level status not exposed" : "Provider status not reported";
  return <section className="panel capability-registry-panel">
    <div className="capability-registry-heading"><SectionHeading eyebrow="DEFAULT REGISTRY SNAPSHOT" title="Capability registry" detail="Registration, saved-plan status, and actual execution are separate states."/><StatusBadge tone={deliveryProvider === false ? "amber" : deliveryProvider === true ? "teal" : "neutral"}>{runtimeLabel}</StatusBadge></div>
    {health ? <ApiDataBoundary timestamp={health.timestamp}><div className="capability-runtime-facts"><span>Module mode: {readableStatus(readString(phase12, "mode"))}</span><span>Indexed plans: {formatCount(readNumber(phase12, "record_count"))}</span><span>Delivery provider: {deliveryProvider === false ? "not available" : deliveryProvider === true ? "reported available" : "not reported"}</span></div></ApiDataBoundary> : <p className="capability-runtime-facts">Live API module status is unavailable in this connection mode.</p>}
      <div className="capability-scope-note"><span>Repository default snapshot from <code>availability_registry.py</code>; its schema has no separate capability description or execution-constraint fields.</span><span>Saved-plan observations below are limited to the retrieved page for the selected learner.</span></div>
      <div className="capability-table-wrap"><table className="capability-table"><thead><tr><th scope="col">Type</th><th scope="col">Default status</th><th scope="col">Provider / content</th><th scope="col">Saved-plan observation</th><th scope="col">Registry reason</th></tr></thead><tbody>{defaultCapabilityRegistry.map((capability) => {
        const definition = representationTaxonomy.find((item) => item.representation_id === capability.representation_id);
        const observed = observations.find((item) => item.representationId === capability.representation_id);
        return <tr key={capability.representation_id}><th scope="row"><strong>{definition?.label ?? capability.representation_id}</strong><code>{capability.representation_id}</code></th><td><CapabilityStatus status={capability.status}/></td><td>{capability.provider_id ?? "No provider ID in default"}<small>{capability.content_ids.length ? `${capability.content_ids.length} content IDs` : "No content IDs in default"}</small></td><td>{observed ? <><span>{observed.statuses.map(readableStatus).join(", ")}</span><small>Observed in {observed.observedPlanCount} plan {observed.observedPlanCount === 1 ? "record" : "records"} on this page</small></> : <span>Not observed on loaded page</span>}</td><td>{capability.reason}</td></tr>;
      })}</tbody></table></div>
  </section>;
}

function CapabilityStatus({ status }: { status: string }) {
  const label = status === "available" ? "Available" : status === "planned" ? "Not configured" : status === "unavailable" ? "Unavailable" : "Unknown";
  const tone = status === "available" ? "teal" : status === "unavailable" ? "amber" : "neutral";
  return <StatusBadge tone={tone}>{label} · {status}</StatusBadge>;
}
