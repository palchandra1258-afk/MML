"use client";

import Link from "next/link";
import { useCallback } from "react";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { EmptyState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiResource } from "@/hooks/use-api-resource";
import type { EvidenceAlignmentLink, EvidenceGroup, EvidenceRecord, JsonValue, LearnerDetail } from "@/lib/api/types";
import { evidenceService } from "@/lib/services/evidence.service";

export function EvidenceRecordDetail({ learner, evidenceId, onSelectEvidence }: { learner: LearnerDetail; evidenceId: string; onSelectEvidence: (id: string) => void }) {
  const loadRecord = useCallback((signal: AbortSignal) => evidenceService.get(learner.learner_id, evidenceId, signal), [evidenceId, learner.learner_id]);
  const detail = useApiResource<EvidenceRecord>(`${learner.learner_id}:evidence-detail:${evidenceId}`, loadRecord);
  return <ApiResourcePanel resource={detail.resource} retry={detail.retry} loadingLabel="Loading evidence detail" emptyTitle="Evidence detail unavailable" emptyMessage="The requested evidence record could not be loaded for this learner.">
    {(record, requestId) => <ApiDataBoundary requestId={requestId}><EvidenceRecordInspection record={record} onSelectEvidence={onSelectEvidence}/></ApiDataBoundary>}
  </ApiResourcePanel>;
}

function EvidenceRecordInspection({ record, onSelectEvidence }: { record: EvidenceRecord; onSelectEvidence: (id: string) => void }) {
  const groups = record.grouping_information ?? [];
  const alignmentLinks = record.alignment_links ?? [];
  const annotationsAvailable = record.grouping_annotations_available === true;
  const relatedEvidenceIds = record.related_evidence_ids ?? [];
  const duplicateCandidates = record.duplicate_candidates ?? [];
  const sourceFields = [
    ["Source dataset", record.provenance.source_dataset],
    ["Source file", record.provenance.source_file ?? "Not supplied"],
    ["Source record ID", record.provenance.source_record_id ?? "Not supplied"],
    ["Source modality", record.provenance.source_modality],
    ["Processing method", record.provenance.processing_method],
    ["Processing version", record.provenance.processing_version],
  ] as const;
  const timestamps = [
    ["Event timestamp", record.temporal.event_timestamp ?? "Not supplied"],
    ["Ingestion timestamp", record.temporal.ingestion_timestamp],
    ["Timestamp source", record.temporal.timestamp_source ?? "Not supplied"],
    ["Temporal precision", record.temporal.temporal_precision],
    ["Sequence number", record.temporal.sequence_number === null ? "Not supplied" : String(record.temporal.sequence_number)],
  ] as const;
  return <article className="evidence-record-inspection">
    <header className="evidence-inspector-heading"><div><p className="eyebrow">EVIDENCE RECORD · {record.schema_version}</p><h3>{record.evidence_id}</h3><span>Learner {record.learner_id} · {record.evidence_type} · {record.provenance.source_modality}</span></div><StatusBadge tone={record.processing.status === "processed" ? "teal" : "amber"}>{record.processing.status}</StatusBadge></header>

    <section className="evidence-provenance-section">
      <SectionHeading eyebrow="PROVENANCE INSPECTOR" title="Source to recorded artifact" detail="Each stage shows fields present in this API response. A blank stage is not treated as an executed operation."/>
      <ol className="evidence-provenance-path">
        <li><PathMarker number="01"/><div><strong>Source</strong><span>{record.provenance.source_dataset}</span><small>{record.provenance.source_file ?? "Source file not supplied"} · record {record.provenance.source_record_id ?? "not supplied"}</small><small>Modality {record.provenance.source_modality} · timestamp source {record.temporal.timestamp_source ?? "not supplied"}</small></div></li>
        <li><PathMarker number="02"/><div><strong>Processing metadata</strong><span>{record.processing.extraction_method || "Extraction method not supplied"}</span><small>Status {record.processing.status} · method {record.provenance.processing_method} · version {record.provenance.processing_version}</small><small>{record.processing.transformation_history.length} recorded transformation entries; see processing details below.</small></div></li>
        <li><PathMarker number="03"/><div><strong>Evidence record</strong><span>{record.evidence_id}</span><small>Schema {record.schema_version} · fingerprint {record.content_fingerprint}</small><small>Processing timestamp {record.processing.processing_timestamp}</small></div></li>
        <li><PathMarker number="04"/><div><strong>Group and alignment annotations</strong><span>{groups.length} embedded group references · {alignmentLinks.length} alignment links</span><small>{annotationsAvailable ? "The API reports grouping annotations available." : "The API does not report grouping annotations available for this record."}</small></div></li>
        <li><PathMarker number="05"/><div><strong>Downstream artifact reference</strong><span>Not exposed on this evidence record</span><small>No evidence-to-artifact reverse-lookup endpoint is present in the API contract.</small></div></li>
      </ol>
      <dl className="evidence-metadata-grid">{sourceFields.map(([label, value]) => <EvidenceDefinition key={label} label={label} value={value}/>)}</dl>
      <dl className="evidence-metadata-grid">{timestamps.map(([label, value]) => <EvidenceDefinition key={label} label={label} value={value}/>)}</dl>
    </section>

    <section className="evidence-processing-section">
      <SectionHeading eyebrow="PROCESSING AND UNCERTAINTY" title="Missingness and quality" detail="These are recorded metadata flags. Missing fields and uncertainty are not interpreted as negative evidence."/>
      <div className="evidence-flag-columns">
        <EvidenceFlags title="Missing processing fields" flags={record.processing.missing_fields}/>
        <EvidenceFlags title="Processing quality flags" flags={record.processing.quality_flags}/>
        <EvidenceFlags title="Evidence uncertainty flags" flags={record.uncertainty.flags}/>
        <EvidenceFlags title="Uncertainty notes" flags={record.uncertainty.notes}/>
      </div>
      {record.uncertainty.processing_confidence !== null && <p className="evidence-confidence-field">Recorded processing confidence: {record.uncertainty.processing_confidence} · source value, not a cognitive or learning-confidence estimate.</p>}
      <details className="evidence-technical-details"><summary>Processing stage and transformation history</summary><dl className="evidence-metadata-grid"><EvidenceDefinition label="Extraction method" value={record.processing.extraction_method}/><EvidenceDefinition label="Processing timestamp" value={record.processing.processing_timestamp}/><EvidenceDefinition label="Provenance processing method" value={record.provenance.processing_method}/><EvidenceDefinition label="Provenance processing version" value={record.provenance.processing_version}/></dl>{record.processing.transformation_history.length ? <ol>{record.processing.transformation_history.map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}</ol> : <p>No transformation history supplied.</p>}</details>
    </section>

    <GroupMembership groups={groups} annotationsAvailable={annotationsAvailable} currentEvidenceId={record.evidence_id} onSelectEvidence={onSelectEvidence}/>
    <AlignmentInspector links={alignmentLinks} onSelectEvidence={onSelectEvidence}/>
    <ConflictAndRelations record={record} onSelectEvidence={onSelectEvidence}/>

    <section className="evidence-content-section">
      <SectionHeading eyebrow="SOURCE PAYLOAD" title="Returned content and record metadata" detail="Raw content is displayed as returned by the API; no OCR, ASR, or semantic interpretation is added."/>
      <details className="evidence-technical-details"><summary>Inspect content fields ({Object.keys(record.content).length})</summary><dl className="evidence-content-fields">{Object.entries(record.content).map(([key, value]) => <EvidenceDefinition key={key} label={key} value={formatJson(value)}/>)}</dl></details>
      <details className="evidence-technical-details"><summary>Inspect all optional evidence metadata</summary><dl className="evidence-content-fields"><EvidenceDefinition label="Session ID" value={record.session_id ?? "Not supplied"}/><EvidenceDefinition label="Related evidence IDs" value={relatedEvidenceIds.join(", ") || "None supplied"}/><EvidenceDefinition label="Duplicate candidate count" value={String(duplicateCandidates.length)}/><EvidenceDefinition label="Grouping annotation availability" value={annotationsAvailable ? "Available" : "Not reported"}/></dl></details>
    </section>

    <section className="evidence-downstream-section">
      <SectionHeading eyebrow="DOWNSTREAM CONTEXT" title="Artifact traceability" detail="The evidence response contains no behavioral, cognitive, plan, or trajectory artifact IDs."/>
      <p>No evidence-specific downstream link is asserted. The API does not expose reverse lookups by evidence ID, so these context links open the selected learner’s views without implying that this record contributed to them.</p>
      <nav className="evidence-context-links" aria-label="Selected learner context views"><Link href="/learner-state">Behavioral state for learner</Link><Link href="/cognitive-state">Latest cognitive estimate</Link><Link href="/representations">Representation plans</Link><Link href="/trajectory">Learning trajectories</Link></nav>
    </section>
  </article>;
}

function GroupMembership({ groups, annotationsAvailable, currentEvidenceId, onSelectEvidence }: { groups: EvidenceGroup[]; annotationsAvailable: boolean; currentEvidenceId: string; onSelectEvidence: (id: string) => void }) {
  return <section className="evidence-record-groups">
    <SectionHeading eyebrow="GROUP MEMBERSHIP" title="Groups attached to this record" detail="Membership and grouping basis are displayed exactly as returned; shared grouping is not semantic equivalence."/>
    {!annotationsAvailable ? <EmptyState title="Group annotations unavailable">This record does not report that group annotations are available.</EmptyState> : groups.length === 0 ? <EmptyState title="No group reference attached">Group annotations are available, but no group record is attached to this evidence response.</EmptyState> : <div className="evidence-record-group-list">{groups.map((group) => <article className="evidence-record-group" key={group.group_id}><div className="evidence-record-group-heading"><div><strong>{group.group_id}</strong><span>{group.grouping_basis}</span></div><StatusBadge tone="neutral">{group.evidence_ids.length} member IDs</StatusBadge></div><dl className="evidence-metadata-grid"><EvidenceDefinition label="Learner" value={group.learner_id}/><EvidenceDefinition label="Session" value={group.session_id ?? "Not supplied"}/><EvidenceDefinition label="Schema version" value={group.schema_version}/><EvidenceDefinition label="Modalities present" value={group.modalities_present.join(", ") || "None reported"}/></dl><div className="evidence-group-members"><h4>Member evidence references</h4>{group.evidence_ids.map((id) => <button type="button" className="text-link" key={id} aria-current={id === currentEvidenceId ? "true" : undefined} onClick={() => onSelectEvidence(id)}>{id}</button>)}</div><ModalityAvailability availability={group.modality_availability}/><EvidenceFlags title="Group uncertainty flags" flags={group.uncertainty_flags}/></article>)}</div>}
  </section>;
}

function AlignmentInspector({ links, onSelectEvidence }: { links: EvidenceAlignmentLink[]; onSelectEvidence: (id: string) => void }) {
  return <section className="evidence-alignment-section">
    <SectionHeading eyebrow="ALIGNMENT INSPECTOR" title="Recorded alignment links" detail="An alignment link is a stored relation, not proof of shared meaning or causation."/>
    {links.length === 0 ? <EmptyState title="No alignment links returned">No alignment link is attached to this record in the current API response. This does not establish that no alignable event exists elsewhere.</EmptyState> : <div className="evidence-alignment-list">{links.map((link, index) => <article className="evidence-alignment-row" key={`${link.left_evidence_id}:${link.right_evidence_id}:${index}`}><div className="evidence-alignment-pair"><button type="button" className="text-link" onClick={() => onSelectEvidence(link.left_evidence_id)}>{link.left_evidence_id}</button><span aria-hidden="true">↔</span><button type="button" className="text-link" onClick={() => onSelectEvidence(link.right_evidence_id)}>{link.right_evidence_id}</button></div><dl className="evidence-metadata-grid"><EvidenceDefinition label="Alignment type" value={link.alignment_type}/><EvidenceDefinition label="Absolute delta" value={link.absolute_delta_ms === null ? "Not supplied" : `${link.absolute_delta_ms} ms`}/><EvidenceDefinition label="Uncertainty" value={link.alignment_uncertainty}/><EvidenceDefinition label="Schema version" value={link.schema_version}/></dl><EvidenceFlags title="Alignment uncertainty flags" flags={link.uncertainty_flags}/></article>)}</div>}
  </section>;
}

function ConflictAndRelations({ record, onSelectEvidence }: { record: EvidenceRecord; onSelectEvidence: (id: string) => void }) {
  const duplicateCandidates = record.duplicate_candidates ?? [];
  const relatedEvidenceIds = record.related_evidence_ids ?? [];
  return <section className="evidence-conflict-section">
    <SectionHeading eyebrow="CONFLICT AND RELATION CHECK" title="Preserved relations and unavailable conflict fields" detail="The contract has no explicit conflict type, status, description, or resolution field."/>
    <div className="evidence-conflict-notice"><StatusBadge tone="neutral">Conflict status not exposed</StatusBadge><p>Possible duplicate candidates and uncertainty flags are preserved below as their own fields. They are not relabeled or resolved as conflicts.</p></div>
    {duplicateCandidates.length > 0 ? <div className="evidence-duplicate-list"><h4>Possible duplicate candidates</h4>{duplicateCandidates.map((candidate, index) => <pre key={index}>{formatJson(candidate)}</pre>)}</div> : <p className="evidence-muted-note">No possible duplicate candidates were included in this response. This is not a conflict-resolution result.</p>}
    {relatedEvidenceIds.length > 0 ? <div className="evidence-related-list"><h4>Related evidence IDs (relation type not supplied)</h4>{relatedEvidenceIds.map((id) => <button className="text-link" type="button" key={id} onClick={() => onSelectEvidence(id)}>{id}</button>)}</div> : <p className="evidence-muted-note">No related evidence IDs were supplied.</p>}
  </section>;
}

function ModalityAvailability({ availability }: { availability: Record<string, import("@/lib/api/types").JsonObject> }) {
  const entries = Object.entries(availability);
  if (!entries.length) return <p className="evidence-muted-note">No per-modality availability map was returned for this group.</p>;
  return <div className="evidence-modality-availability"><h4>Group modality availability</h4><ul>{entries.map(([modality, details]) => <li key={modality}><span>{modality}</span><StatusBadge tone={details.status === "available" ? "teal" : "amber"}>{String(details.status ?? "unknown")}</StatusBadge><small>{String(details.reason ?? "")}</small></li>)}</ul></div>;
}

function EvidenceFlags({ title, flags }: { title: string; flags: string[] }) {
  return <div className="evidence-flags"><h4>{title}</h4>{flags.length ? <ul>{flags.map((flag, index) => <li key={`${flag}-${index}`}>{flag}</li>)}</ul> : <p>None supplied.</p>}</div>;
}

function PathMarker({ number }: { number: string }) {
  return <span className="evidence-path-marker">{number}</span>;
}

function EvidenceDefinition({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}

function formatJson(value: JsonValue): string {
  if (value === null) return "null";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value, null, 2) ?? String(value);
}
