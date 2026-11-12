"use client";

import { useCallback, useMemo, useState } from "react";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { EmptyState, DataSourceLabel, LoadingState } from "@/components/shared/data-states";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { LearnerRecordPicker } from "@/components/learner/learner-record-picker";
import { ResearchDataNotice, SelectedLearnerSummary } from "@/components/learner/learner-page-common";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiHealth } from "@/hooks/use-api-health";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import type { ApiPage, EvidenceRecord, HealthData, LearnerDetail } from "@/lib/api/types";
import { formatCount, readNumber, readableStatus } from "@/lib/learner/presentation";
import { evidenceService } from "@/lib/services/evidence.service";
import { filterEvidenceRecords, summarizeEvidencePage, type EvidenceAlignmentFilter, type EvidenceDuplicateFilter, type EvidenceFilters, type EvidenceTypeFilter } from "@/lib/evidence/explorer";
import { EvidenceRecordDetail } from "@/components/evidence/evidence-record-detail";

const PAGE_SIZE = 25;
const evidenceTypes: EvidenceRecord["evidence_type"][] = ["interaction", "temporal_history", "text", "audio", "visual"];
const EMPTY_FILTERS: EvidenceFilters = { query: "", evidenceType: "all", sourceModality: "all", sourceDataset: "all", groupId: "all", processingStatus: "all", alignment: "all", duplicates: "all", dateFrom: "", dateTo: "" };

export function EvidenceExplorerPage() {
  const { learner } = useLearnerSelection();
  const { state: connection, health } = useApiHealth();
  const kind = connection === "connected" ? "api" : "unavailable";
  const detail = connection === "connected" ? "Evidence returned by the live API" : connection === "mock" ? "Mock mode · no synthetic evidence fixture" : connection === "connecting" ? "Checking live API availability" : "Live evidence unavailable";
  const canReadEvidence = Boolean(learner && learner.available_data.includes("phase10_evidence") && connection === "connected");

  return <div className="evidence-explorer-page">
    <header className="evidence-page-heading"><div><p className="eyebrow">RESEARCH EVIDENCE</p><h2>Evidence explorer<span className="welcome-period">.</span></h2><p>Inspect evidence records, their source and processing history, group membership, alignment metadata, gaps, and explicit artifact references.</p></div><DataSourceLabel kind={kind} detail={detail}/></header>
    <ResearchDataNotice>The published Phase 10 coverage run contains 1,000 EdNet interaction records. Text, audio, and visual adapters were exercised with synthetic fixtures; those fixtures are not learner records and are not shown here. Counts in this view are labeled by their API or page scope.</ResearchDataNotice>

    {connection === "connecting" && <LoadingState label="Checking evidence API availability"/>}
    {connection === "mock" && <EmptyState title="Evidence fixtures are not available in mock mode">The separate synthetic dashboard walkthrough is not an evidence record. No synthetic evidence is substituted into this explorer.</EmptyState>}
    {(connection === "disconnected" || connection === "error") && <EmptyState title="Live evidence is unavailable">The API is {connection}. Retry from the connection control after the backend is available. Evidence records are not replaced with demo data.</EmptyState>}
    {connection === "connected" && <LearnerRecordPicker/>}
    {connection === "connected" && learner && <SelectedLearnerSummary learner={learner}/>}
    {connection === "connected" && learner && !learner.available_data.includes("phase10_evidence") && <EmptyState title="No evidence records are indexed for this learner">The learner detail response does not list Phase 10 evidence for this record.</EmptyState>}
    {canReadEvidence && learner && <EvidenceExplorerForLearner key={learner.learner_id} learner={learner} health={health ?? null}/>}
  </div>;
}

function EvidenceExplorerForLearner({ learner, health }: { learner: LearnerDetail; health: HealthData | null }) {
  const learnerId = learner.learner_id;
  const [offset, setOffset] = useState(0);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [filters, setFilters] = useState<EvidenceFilters>(EMPTY_FILTERS);
  const listKey = `${learnerId}:evidence:${filters.evidenceType}:${offset}`;
  const loadPage = useCallback((signal: AbortSignal) => evidenceService.list(learnerId, {
    limit: PAGE_SIZE,
    offset,
    evidenceType: filters.evidenceType === "all" ? undefined : filters.evidenceType,
    signal,
  }), [filters.evidenceType, learnerId, offset]);
  const pageResource = useApiResource<ApiPage<EvidenceRecord>>(listKey, loadPage);
  const page = pageResource.resource.status === "success" ? pageResource.resource.data : undefined;
  const pageSummary = useMemo(() => summarizeEvidencePage(page?.items ?? []), [page]);
  const visibleRecords = useMemo(() => filterEvidenceRecords(page?.items ?? [], filters), [filters, page]);
  const pageGroups = useMemo(() => pageSummary.uniqueGroups, [pageSummary.uniqueGroups]);
  const activeEvidenceId = selectedEvidenceId || page?.items[0]?.evidence_id || "";
  const values = page?.items ?? [];
  const modalities = sortedUnique(values.map((record) => record.provenance.source_modality));
  const sources = sortedUnique(values.map((record) => record.provenance.source_dataset));
  const groupIds = sortedUnique(values.flatMap((record) => (record.grouping_information ?? []).map((group) => group.group_id)));
  const processingStatuses = sortedUnique(values.map((record) => record.processing.status));

  const updateFilter = <K extends keyof EvidenceFilters>(key: K, value: EvidenceFilters[K]) => setFilters((current) => ({ ...current, [key]: value }));
  const resetFilters = () => { setFilters({ ...EMPTY_FILTERS }); setOffset(0); setSelectedGroupId(""); };
  const changeEvidenceType = (value: EvidenceTypeFilter) => { updateFilter("evidenceType", value); setOffset(0); setSelectedGroupId(""); };

  const renderPage = (data: ApiPage<EvidenceRecord>, requestId: string | null) => <ApiDataBoundary requestId={requestId}>
    <EvidenceOverview page={data} summary={pageSummary} health={health}/>
    <ModalityCoverage summary={pageSummary}/>
    <EvidenceFiltersPanel filters={filters} modalities={modalities} sources={sources} groups={groupIds} processingStatuses={processingStatuses} onChange={updateFilter} onTypeChange={changeEvidenceType} onReset={resetFilters}/>
    <p className="evidence-filter-scope">Text, modality, source, group, processing, alignment, duplicate-candidate, and date filters apply to the {data.items.length} records returned on this API page. Evidence type is also sent to the backend. Learner scope is {learnerId}; filters do not search other learners or pages.</p>
    <div className="evidence-pagination"><button type="button" className="button button--secondary" disabled={data.offset === 0 || pageResource.resource.status === "loading"} onClick={() => { setOffset((current) => Math.max(0, current - PAGE_SIZE)); setSelectedGroupId(""); }}>Previous</button><span>Page {Math.floor(data.offset / Math.max(data.limit, 1)) + 1} · {data.items.length ? `${data.offset + 1}–${Math.min(data.offset + data.items.length, data.total)}` : "0 records"} of {data.total.toLocaleString()} API matches</span><button type="button" className="button button--secondary" disabled={!data.has_more || pageResource.resource.status === "loading"} onClick={() => { setOffset((current) => current + PAGE_SIZE); setSelectedGroupId(""); }}>Next</button></div>

    <section className="evidence-browser-layout" aria-label="Evidence records and selected record detail">
      <div className="evidence-index-panel">
        <SectionHeading eyebrow="EVIDENCE INDEX" title="Evidence records" detail="Select a returned record to inspect the full API detail."/>
        <p className="evidence-page-count">{visibleRecords.length} matching this page’s filters · {data.items.length} records returned on page</p>
        {activeEvidenceId && !visibleRecords.some((record) => record.evidence_id === activeEvidenceId) && <p className="evidence-filter-scope">The selected record is outside the current filters or page; its detail remains open for this learner.</p>}
        {visibleRecords.length === 0 ? <EmptyState title={data.items.length ? "No records match these filters" : "No evidence records on this page"}>{data.items.length ? "Reset filters or move to another API page. The current API response remains unchanged." : "The backend returned no evidence records for this learner and query."}</EmptyState> : <ul className="evidence-record-list" aria-label="Evidence records on the current page">{visibleRecords.map((record) => <li key={record.evidence_id}><button type="button" className={`evidence-record-choice ${activeEvidenceId === record.evidence_id ? "evidence-record-choice--active" : ""}`} onClick={() => setSelectedEvidenceId(record.evidence_id)} aria-pressed={activeEvidenceId === record.evidence_id}>
          <span className="evidence-record-choice-heading"><strong>{record.evidence_id}</strong><StatusBadge tone={record.processing.status === "processed" ? "teal" : "amber"}>{readableStatus(record.processing.status)}</StatusBadge></span>
          <span className="evidence-record-choice-tags"><StatusBadge tone="neutral">{record.evidence_type}</StatusBadge><StatusBadge tone="neutral">{record.provenance.source_modality}</StatusBadge></span>
          <span className="evidence-record-choice-meta">{record.provenance.source_dataset} · {record.temporal.timestamp_source ?? "Timestamp source not supplied"}</span>
          <span className="evidence-record-choice-meta">{record.grouping_information?.length ?? 0} groups · {record.alignment_links?.length ?? 0} alignment links · {record.learner_id}</span>
        </button></li>)}</ul>}
      </div>
      <div className="evidence-inspector-panel">
        {activeEvidenceId ? <EvidenceRecordDetail key={`${learnerId}:${activeEvidenceId}`} learner={learner} evidenceId={activeEvidenceId} onSelectEvidence={setSelectedEvidenceId}/> : <EmptyState title="Select an evidence record">Choose a record to inspect provenance, processing, group and alignment references.</EmptyState>}
      </div>
    </section>

    <EvidenceGroupExplorer groups={pageGroups} recordCount={data.items.length} annotationsAvailable={data.items.some((record) => record.grouping_annotations_available === true)} selectedGroupId={selectedGroupId} onSelectGroup={(group) => { setSelectedGroupId(group.group_id); setSelectedEvidenceId(group.evidence_ids[0] ?? ""); }} onSelectEvidence={setSelectedEvidenceId}/>
    <ResearchDataNotice>Conflict status is not exposed in the EvidenceRecord API schema. Possible duplicate candidates are shown separately and are not treated as conflicts. Evidence records also contain no downstream artifact IDs; this interface does not invent reverse links to behavioral states, cognitive estimates, plans, or trajectories.</ResearchDataNotice>
  </ApiDataBoundary>;

  return <section className="panel evidence-main-panel">
    <SectionHeading eyebrow="PHASE 10 EVIDENCE" title="Evidence collection" detail="Evidence and group totals from API health are separate from the records returned for this learner page."/>
    <ApiResourcePanel resource={pageResource.resource} retry={pageResource.retry} loadingLabel="Loading evidence records" emptyTitle="No evidence collection is available" emptyMessage="The evidence service returned no records for this learner and query.">{renderPage}</ApiResourcePanel>
  </section>;
}

function EvidenceOverview({ page, summary, health }: { page: ApiPage<EvidenceRecord>; summary: ReturnType<typeof summarizeEvidencePage>; health: HealthData | null }) {
  const evidenceTotal = readNumber(health?.modules.phase10_evidence, "record_count");
  const groupTotal = readNumber(health?.modules.phase10_grouping, "record_count");
  const hasGroupAnnotations = page.items.some((record) => record.grouping_annotations_available);
  return <section className="evidence-overview-metrics" aria-label="Evidence collection summary">
    <EvidenceMetric label="Records retrieved so far" value={formatCount(summary.returned)} detail={`Current page only · offset ${page.offset}`}/>
    <EvidenceMetric label="Learner API total" value={formatCount(page.total)} detail="Selected learner and type filter"/>
    <EvidenceMetric label="Backend indexed records" value={formatCount(evidenceTotal)} detail="Health endpoint · all learners"/>
    <EvidenceMetric label="Groups in this page" value={formatCount(summary.uniqueGroups.length)} detail="Unique embedded group IDs"/>
    <EvidenceMetric label="Backend indexed groups" value={formatCount(groupTotal)} detail="Health endpoint · all learners"/>
    <EvidenceMetric label="With provenance" value={formatCount(summary.recordsWithProvenance)} detail="Returned page"/>
    <EvidenceMetric label="Missing processing fields" value={formatCount(summary.recordsWithMissingFields)} detail="Returned page"/>
    <EvidenceMetric label="With alignment links" value={formatCount(summary.recordsWithAlignment)} detail="Returned page"/>
    <EvidenceMetric label="Conflict status" value="Not exposed" detail="No conflict field or endpoint"/>
    <EvidenceMetric label="Group annotations" value={hasGroupAnnotations ? "Available" : page.items.length ? "Not reported" : "No records"} detail="Evidence responses on page"/>
  </section>;
}

function EvidenceMetric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <div className="evidence-metric"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function ModalityCoverage({ summary }: { summary: ReturnType<typeof summarizeEvidencePage> }) {
  const modalities = Object.entries(summary.sourceModalities).sort(([left], [right]) => left.localeCompare(right));
  const types = Object.entries(summary.evidenceTypes).sort(([left], [right]) => left.localeCompare(right));
  const sources = Object.entries(summary.sourceDatasets).sort(([left], [right]) => left.localeCompare(right));
  return <section className="evidence-modality-panel">
    <SectionHeading eyebrow="RETURNED RECORDS ONLY" title="Modality and source coverage" detail="Counts describe this API page. A zero or absent category here does not describe the global dataset."/>
    <div className="evidence-coverage-grid">
      <CoverageList title="Source modality" rows={modalities}/>
      <CoverageList title="Evidence type" rows={types}/>
      <CoverageList title="Source dataset" rows={sources}/>
      <div className="evidence-coverage-list"><h4>Metadata coverage</h4><p>{summary.recordsWithMissingFields} records report missing processing fields.</p><p>{summary.recordsWithQualityFlags} records report processing quality flags.</p><p>{summary.recordsWithPossibleDuplicates} records include possible duplicate candidates; these are not conflict records.</p></div>
    </div>
  </section>;
}

function CoverageList({ title, rows }: { title: string; rows: [string, number][] }) {
  return <div className="evidence-coverage-list"><h4>{title}</h4>{rows.length ? <ul>{rows.map(([label, count]) => <li key={label}><span>{label}</span><strong>{count}</strong></li>)}</ul> : <p>No values were returned on this page.</p>}</div>;
}

function EvidenceFiltersPanel({ filters, modalities, sources, groups, processingStatuses, onChange, onTypeChange, onReset }: {
  filters: EvidenceFilters;
  modalities: string[];
  sources: string[];
  groups: string[];
  processingStatuses: string[];
  onChange: <K extends keyof EvidenceFilters>(key: K, value: EvidenceFilters[K]) => void;
  onTypeChange: (value: EvidenceTypeFilter) => void;
  onReset: () => void;
}) {
  return <section className="evidence-filters" aria-label="Filter evidence records">
    <label className="evidence-search-field" htmlFor="evidence-search">Search this page<span>IDs, source, processing, and returned metadata</span><input id="evidence-search" type="search" value={filters.query} onChange={(event) => onChange("query", event.target.value)} placeholder="Search evidence, learner, source…"/></label>
    <label htmlFor="evidence-type-filter">Evidence type<select id="evidence-type-filter" value={filters.evidenceType} onChange={(event) => onTypeChange(event.target.value as EvidenceTypeFilter)}><option value="all">All types</option>{evidenceTypes.map((type) => <option value={type} key={type}>{type}</option>)}</select><small>Type is sent to the API.</small></label>
    <FilterSelect id="evidence-modality-filter" label="Source modality" value={filters.sourceModality} values={modalities} onChange={(value) => onChange("sourceModality", value)}/>
    <FilterSelect id="evidence-source-filter" label="Source dataset" value={filters.sourceDataset} values={sources} onChange={(value) => onChange("sourceDataset", value)}/>
    <FilterSelect id="evidence-group-filter" label="Group ID" value={filters.groupId} values={groups} onChange={(value) => onChange("groupId", value)}/>
    <FilterSelect id="evidence-processing-filter" label="Processing status" value={filters.processingStatus} values={processingStatuses} onChange={(value) => onChange("processingStatus", value)}/>
    <label htmlFor="evidence-alignment-filter">Alignment data<select id="evidence-alignment-filter" value={filters.alignment} onChange={(event) => onChange("alignment", event.target.value as EvidenceAlignmentFilter)}><option value="all">All records</option><option value="linked">Has alignment links</option><option value="uncertainty">Link has uncertainty flag</option><option value="no-links">No links in returned record</option></select></label>
    <label htmlFor="evidence-duplicate-filter">Possible duplicates<select id="evidence-duplicate-filter" value={filters.duplicates} onChange={(event) => onChange("duplicates", event.target.value as EvidenceDuplicateFilter)}><option value="all">All records</option><option value="candidates">Has duplicate candidates</option><option value="no-candidates">No duplicate candidates</option></select></label>
    <label htmlFor="evidence-date-from">Ingested from<input id="evidence-date-from" type="date" value={filters.dateFrom} onChange={(event) => onChange("dateFrom", event.target.value)}/></label>
    <label htmlFor="evidence-date-to">Ingested through<input id="evidence-date-to" type="date" value={filters.dateTo} onChange={(event) => onChange("dateTo", event.target.value)}/></label>
    <button type="button" className="button button--secondary evidence-filter-reset" onClick={onReset} disabled={JSON.stringify(filters) === JSON.stringify(EMPTY_FILTERS)}>Reset filters</button>
  </section>;
}

function FilterSelect({ id, label, value, values, onChange }: { id: string; label: string; value: string; values: string[]; onChange: (value: string) => void }) {
  const options = [...new Set([...values, ...(value === "all" ? [] : [value])])].filter((item) => item !== "all").sort();
  return <label htmlFor={id}>{label}<select id={id} value={value} onChange={(event) => onChange(event.target.value)}><option value="all">All values</option>{options.map((item) => <option value={item} key={item}>{item}</option>)}</select></label>;
}

function EvidenceGroupExplorer({ groups, recordCount, annotationsAvailable, selectedGroupId, onSelectGroup, onSelectEvidence }: {
  groups: ReturnType<typeof summarizeEvidencePage>["uniqueGroups"];
  recordCount: number;
  annotationsAvailable: boolean;
  selectedGroupId: string;
  onSelectGroup: (group: ReturnType<typeof summarizeEvidencePage>["uniqueGroups"][number]) => void;
  onSelectEvidence: (id: string) => void;
}) {
  const selected = groups.find((group) => group.group_id === selectedGroupId);
  return <section className="evidence-group-explorer">
    <SectionHeading eyebrow="EMBEDDED GROUP ANNOTATIONS" title="Evidence groups" detail="Group records are embedded in evidence responses; no standalone group-list endpoint is exposed."/>
    {recordCount === 0 ? <EmptyState title="No evidence records to group">The evidence API returned no records for this learner and type query.</EmptyState> : !annotationsAvailable ? <EmptyState title="Group annotations are unavailable">The returned records do not report grouping annotations. This is distinct from evidence records having no group membership.</EmptyState> : groups.length === 0 ? <EmptyState title="No group records on this page">Grouping annotations are available, but no group ID was attached to the returned records.</EmptyState> : <div className="evidence-group-layout">
      <ul className="evidence-group-list" aria-label="Groups found on the current API page">{groups.map((group) => <li key={group.group_id}><button type="button" aria-pressed={selectedGroupId === group.group_id} className={`evidence-group-choice ${selectedGroupId === group.group_id ? "evidence-group-choice--active" : ""}`} onClick={() => onSelectGroup(group)}><strong>{group.group_id}</strong><span>{group.evidence_ids.length} member IDs · {group.modalities_present.join(", ") || "No modalities reported"}</span><small>{group.grouping_basis}</small></button></li>)}</ul>
      {selected ? <article className="evidence-group-detail"><div><span className="eyebrow">SELECTED GROUP</span><h3>{selected.group_id}</h3></div><dl className="evidence-metadata-grid"><EvidenceDefinition label="Learner" value={selected.learner_id}/><EvidenceDefinition label="Session" value={selected.session_id ?? "Not supplied"}/><EvidenceDefinition label="Schema version" value={selected.schema_version}/><EvidenceDefinition label="Grouping basis" value={selected.grouping_basis}/></dl><div className="evidence-group-members"><h4>Member evidence references</h4>{selected.evidence_ids.length ? selected.evidence_ids.map((id) => <button type="button" className="text-link" key={id} onClick={() => onSelectEvidence(id)}>{id}</button>) : <p>No member IDs supplied.</p>}</div><ModalityAvailability availability={selected.modality_availability}/><GroupFlags title="Group uncertainty flags" flags={selected.uncertainty_flags}/></article> : <EmptyState title="Select a group">Choose a group ID from the current page to inspect member references and modality availability.</EmptyState>}
    </div>}
  </section>;
}

function ModalityAvailability({ availability }: { availability: Record<string, import("@/lib/api/types").JsonObject> }) {
  const entries = Object.entries(availability);
  if (!entries.length) return <p className="evidence-muted-note">Per-modality availability was not supplied for this group.</p>;
  return <div className="evidence-modality-availability"><h4>Group modality availability</h4><ul>{entries.map(([modality, details]) => <li key={modality}><span>{modality}</span><StatusBadge tone={details.status === "available" ? "teal" : "amber"}>{String(details.status ?? "unknown")}</StatusBadge><small>{String(details.reason ?? "")}</small></li>)}</ul></div>;
}

function GroupFlags({ title, flags }: { title: string; flags: string[] }) {
  return <div className="evidence-flags"><h4>{title}</h4>{flags.length ? <ul>{flags.map((flag, index) => <li key={`${flag}-${index}`}>{flag}</li>)}</ul> : <p>None supplied.</p>}</div>;
}

function EvidenceDefinition({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}

function sortedUnique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right));
}
