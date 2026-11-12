import type { EvidenceGroup, EvidenceRecord } from "../api/types";

export type EvidenceTypeFilter = "all" | EvidenceRecord["evidence_type"];
export type EvidenceAlignmentFilter = "all" | "linked" | "uncertainty" | "no-links";
export type EvidenceDuplicateFilter = "all" | "candidates" | "no-candidates";

export interface EvidenceFilters {
  query: string;
  evidenceType: EvidenceTypeFilter;
  sourceModality: string;
  sourceDataset: string;
  groupId: string;
  processingStatus: string;
  alignment: EvidenceAlignmentFilter;
  duplicates: EvidenceDuplicateFilter;
  dateFrom: string;
  dateTo: string;
}

export interface EvidencePageSummary {
  returned: number;
  evidenceTypes: Record<string, number>;
  sourceModalities: Record<string, number>;
  sourceDatasets: Record<string, number>;
  recordsWithProvenance: number;
  recordsWithMissingFields: number;
  recordsWithQualityFlags: number;
  recordsWithAlignment: number;
  recordsWithPossibleDuplicates: number;
  recordsWithGroups: number;
  uniqueGroups: EvidenceGroup[];
}

export function filterEvidenceRecords(records: EvidenceRecord[], filters: EvidenceFilters): EvidenceRecord[] {
  const query = filters.query.trim().toLocaleLowerCase();
  return records.filter((record) => {
    if (filters.evidenceType !== "all" && record.evidence_type !== filters.evidenceType) return false;
    if (filters.sourceModality !== "all" && record.provenance.source_modality !== filters.sourceModality) return false;
    if (filters.sourceDataset !== "all" && record.provenance.source_dataset !== filters.sourceDataset) return false;
    if (filters.groupId !== "all" && !(record.grouping_information ?? []).some((group) => group.group_id === filters.groupId)) return false;
    if (filters.processingStatus !== "all" && record.processing.status !== filters.processingStatus) return false;
    if (filters.alignment === "linked" && (record.alignment_links ?? []).length === 0) return false;
    if (filters.alignment === "uncertainty" && !(record.alignment_links ?? []).some((link) => (link.uncertainty_flags ?? []).length > 0 || isUncertain(link.alignment_uncertainty))) return false;
    if (filters.alignment === "no-links" && (record.alignment_links ?? []).length > 0) return false;
    if (filters.duplicates === "candidates" && (record.duplicate_candidates ?? []).length === 0) return false;
    if (filters.duplicates === "no-candidates" && (record.duplicate_candidates ?? []).length > 0) return false;
    const ingestionDate = record.temporal.ingestion_timestamp.slice(0, 10);
    if (filters.dateFrom && ingestionDate < filters.dateFrom) return false;
    if (filters.dateTo && ingestionDate > filters.dateTo) return false;
    if (query && !JSON.stringify(record).toLocaleLowerCase().includes(query)) return false;
    return true;
  });
}

export function summarizeEvidencePage(records: EvidenceRecord[]): EvidencePageSummary {
  const uniqueGroups = collectEvidenceGroups(records);
  return {
    returned: records.length,
    evidenceTypes: countValues(records.map((record) => record.evidence_type)),
    sourceModalities: countValues(records.map((record) => record.provenance.source_modality)),
    sourceDatasets: countValues(records.map((record) => record.provenance.source_dataset)),
    recordsWithProvenance: records.filter((record) => Boolean(record.provenance.source_dataset && record.provenance.source_modality && record.provenance.processing_method && record.provenance.processing_version)).length,
    recordsWithMissingFields: records.filter((record) => record.processing.missing_fields.length > 0).length,
    recordsWithQualityFlags: records.filter((record) => record.processing.quality_flags.length > 0).length,
    recordsWithAlignment: records.filter((record) => (record.alignment_links ?? []).length > 0).length,
    recordsWithPossibleDuplicates: records.filter((record) => (record.duplicate_candidates ?? []).length > 0).length,
    recordsWithGroups: records.filter((record) => (record.grouping_information ?? []).length > 0).length,
    uniqueGroups,
  };
}

export function collectEvidenceGroups(records: EvidenceRecord[]): EvidenceGroup[] {
  const byId = new Map<string, EvidenceGroup>();
  for (const record of records) {
    for (const group of record.grouping_information ?? []) {
      if (!byId.has(group.group_id)) byId.set(group.group_id, group);
    }
  }
  return [...byId.values()];
}

function countValues(values: string[]): Record<string, number> {
  return values.reduce<Record<string, number>>((counts, value) => {
    if (value) counts[value] = (counts[value] ?? 0) + 1;
    return counts;
  }, {});
}

function isUncertain(value: string): boolean {
  const normalized = value.toLocaleLowerCase();
  return normalized.includes("uncertain") || normalized.includes("unresolved") || normalized.includes("unknown");
}
