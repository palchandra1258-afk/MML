const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const test = require("node:test");
const { filterEvidenceRecords, summarizeEvidencePage, collectEvidenceGroups } = require("../../.api-test-dist/lib/evidence/explorer.js");
const { createEvidenceService } = require("../../.api-test-dist/lib/services/evidence.service.js");

const group = (groupId, evidenceIds = ["E-1"]) => ({
  schema_version: "1.0",
  group_id: groupId,
  learner_id: "L-1",
  session_id: "session-1",
  evidence_ids: evidenceIds,
  grouping_basis: "singleton_no_shared_session",
  modalities_present: ["interaction"],
  modality_availability: { interaction: { status: "available", reason: null }, audio: { status: "unavailable", reason: "No audio item" } },
  alignment_links: [],
  uncertainty_flags: ["no_session_identifier_available"],
});

function evidence(id, overrides = {}) {
  return {
    evidence_id: id,
    learner_id: "L-1",
    schema_version: "1.0",
    session_id: "session-1",
    evidence_type: "interaction",
    temporal: { event_timestamp: "1519924149973", ingestion_timestamp: "2026-11-06T10:13:30Z", sequence_number: 1, temporal_precision: "millisecond", timestamp_source: "EdNet shifted question-given timestamp" },
    provenance: { source_dataset: "EdNet-KT1", source_file: "KT1/u1.csv", source_record_id: "u1:1", source_modality: "interaction", processing_method: "processed_csv_field_mapping", processing_version: "1.0" },
    content: { question_id: "q-1", correctness: 1, skill_ids: [id === "E-2" ? "skill-b" : "skill-a"] },
    processing: { status: "processed", processing_timestamp: "2026-11-06T10:13:30Z", extraction_method: "processed_csv_field_mapping", quality_flags: [], missing_fields: [], transformation_history: ["preserved source timestamp text"] },
    uncertainty: { flags: ["behavioral_outcome_not_cognitive_label"], processing_confidence: null, notes: ["Publisher-shifted timestamp"] },
    content_fingerprint: "fingerprint-1",
    related_evidence_ids: [],
    duplicate_candidates: [],
    grouping_information: [group("G-1", [id])],
    alignment_links: [],
    grouping_annotations_available: true,
    ...overrides,
  };
}

const filters = { query: "", evidenceType: "all", sourceModality: "all", sourceDataset: "all", groupId: "all", processingStatus: "all", alignment: "all", duplicates: "all", dateFrom: "", dateTo: "" };

test("evidence filters search returned fields and respect modality, source, group, status, and date scope", () => {
  const interaction = evidence("E-1");
  const visual = evidence("E-2", {
    evidence_type: "visual",
    temporal: { ...interaction.temporal, ingestion_timestamp: "2026-11-09T10:00:00Z" },
    provenance: { ...interaction.provenance, source_dataset: "Synthetic fixture", source_modality: "visual" },
    grouping_information: [],
  });
  assert.deepEqual(filterEvidenceRecords([interaction, visual], { ...filters, query: "skill-a" }), [interaction]);
  assert.deepEqual(filterEvidenceRecords([interaction, visual], { ...filters, evidenceType: "visual", sourceModality: "visual", sourceDataset: "Synthetic fixture" }), [visual]);
  assert.deepEqual(filterEvidenceRecords([interaction, visual], { ...filters, groupId: "G-1", dateFrom: "2026-11-06", dateTo: "2026-11-07" }), [interaction]);
  assert.deepEqual(filterEvidenceRecords([interaction], { ...filters, processingStatus: "failed" }), []);
  assert.deepEqual(filterEvidenceRecords([], filters), []);
});

test("alignment uncertainty and possible duplicates are filtered as distinct fields", () => {
  const aligned = evidence("E-align", {
    alignment_links: [{ schema_version: "1.0", left_evidence_id: "E-align", right_evidence_id: "E-peer", alignment_type: "timestamp_candidate", absolute_delta_ms: 10, alignment_uncertainty: "high", uncertainty_flags: ["low_temporal_precision"] }],
    duplicate_candidates: [{ evidence_id: "E-peer", candidate_basis: "content_fingerprint" }],
  });
  const unlinked = evidence("E-none");
  assert.deepEqual(filterEvidenceRecords([aligned, unlinked], { ...filters, alignment: "linked" }), [aligned]);
  assert.deepEqual(filterEvidenceRecords([aligned, unlinked], { ...filters, alignment: "uncertainty" }), [aligned]);
  assert.deepEqual(filterEvidenceRecords([aligned, unlinked], { ...filters, alignment: "no-links" }), [unlinked]);
  assert.deepEqual(filterEvidenceRecords([aligned, unlinked], { ...filters, duplicates: "candidates" }), [aligned]);
  assert.deepEqual(filterEvidenceRecords([aligned, unlinked], { ...filters, duplicates: "no-candidates" }), [unlinked]);
});

test("page summary counts only returned records and deduplicates their embedded groups", () => {
  const first = evidence("E-1");
  const second = evidence("E-2", { grouping_information: [group("G-1", ["E-1", "E-2"])] });
  const incomplete = evidence("E-3", {
    provenance: { ...first.provenance, source_file: null, source_record_id: null },
    processing: { ...first.processing, missing_fields: ["source_record_id"], quality_flags: ["partial_source_row"] },
    grouping_information: [],
    grouping_annotations_available: true,
  });
  const summary = summarizeEvidencePage([first, second, incomplete]);
  assert.equal(summary.returned, 3);
  assert.deepEqual(summary.evidenceTypes, { interaction: 3 });
  assert.deepEqual(summary.sourceModalities, { interaction: 3 });
  assert.equal(summary.recordsWithGroups, 2);
  assert.equal(summary.uniqueGroups.length, 1);
  assert.equal(summary.recordsWithMissingFields, 1);
  assert.equal(summary.recordsWithQualityFlags, 1);
  assert.deepEqual(collectEvidenceGroups([]), []);
});

test("evidence service uses only the contracted list filter and learner-scoped detail route", async () => {
  const calls = [];
  const client = { get: async (path, options) => { calls.push({ path, options }); return { data: undefined, requestId: "req-evidence", status: 200 }; } };
  const service = createEvidenceService(client);
  await service.list("L-1", { limit: 25, offset: 25, evidenceType: "interaction" });
  await service.get("L-1", "E-1");
  assert.equal(calls[0].path, "/learners/L-1/evidence?limit=25&offset=25&evidence_type=interaction");
  assert.equal(calls[1].path, "/learners/L-1/evidence/E-1");
  assert.equal(calls[0].options.signal, undefined);
});

test("evidence route documents real/mock separation, non-inferred relations, and responsive navigation", () => {
  const route = readFileSync(resolve(__dirname, "../../app/[section]/page.tsx"), "utf8");
  const page = readFileSync(resolve(__dirname, "../../components/evidence/evidence-explorer-page.tsx"), "utf8");
  const detail = readFileSync(resolve(__dirname, "../../components/evidence/evidence-record-detail.tsx"), "utf8");
  const styles = readFileSync(resolve(__dirname, "../../app/globals.css"), "utf8");
  assert.match(route, /section === "evidence"\) return <EvidenceExplorerPage/);
  assert.match(page, /no synthetic evidence fixture/);
  assert.match(page, /filters do not search other learners or pages/);
  assert.match(page, /data\.has_more/);
  assert.match(page, /No evidence records to group/);
  assert.match(page, /Conflict status is not exposed/);
  assert.match(detail, /evidenceService\.get/);
  assert.match(detail, /No evidence-specific downstream link is asserted/);
  assert.match(detail, /not relabeled or resolved as conflicts/);
  assert.match(detail, /not proof of shared meaning or causation/);
  assert.match(styles, /@media \(max-width: 680px\)/);
  assert.match(styles, /\.evidence-record-list/);
});
