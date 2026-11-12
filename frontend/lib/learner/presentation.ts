import type { CognitiveStateRecord, EvidenceRecord, JsonObject, JsonValue, TrajectoryRecord } from "../api/types";

export function artifactResourceKey(learnerId: string, availableData: string[], artifact: string): string | null {
  return availableData.includes(artifact) ? `${learnerId}:${artifact}` : null;
}

export function readObject(value: JsonValue | undefined): JsonObject | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value : undefined;
}

export function readString(value: JsonObject | undefined, key: string): string | undefined {
  const field = value?.[key];
  return typeof field === "string" ? field : undefined;
}

export function readNumber(value: JsonObject | undefined, key: string): number | undefined {
  const field = value?.[key];
  return typeof field === "number" && Number.isFinite(field) ? field : undefined;
}

export function readStringList(value: JsonObject | undefined, key: string): string[] {
  const field = value?.[key];
  return Array.isArray(field) ? field.filter((entry): entry is string => typeof entry === "string") : [];
}

export function formatPercentage(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "Not reported";
}

export function formatInterval(value: JsonValue | undefined): string {
  if (!Array.isArray(value) || value.length !== 2) return "Not reported";
  const lower = value[0];
  const upper = value[1];
  if (typeof lower !== "number" || !Number.isFinite(lower) || typeof upper !== "number" || !Number.isFinite(upper)) return "Not reported";
  return `${formatPercentage(lower)}–${formatPercentage(upper)}`;
}

export function formatCount(value: number | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString() : "Not reported";
}

export function readableStatus(value: string | undefined): string {
  if (!value) return "Not reported";
  return value.toLowerCase().replaceAll("_", " ");
}

export function evidenceForConcept(records: EvidenceRecord[], conceptId: string): EvidenceRecord[] {
  return records.filter((record) => {
    const skillIds = record.content.skill_ids;
    return Array.isArray(skillIds) && skillIds.some((skillId) => skillId === conceptId);
  });
}

export function selectedConcept(concepts: JsonObject[], selectedId: string): JsonObject | undefined {
  return concepts.find((concept) => readString(concept, "concept_id") === selectedId) ?? concepts[0];
}

export function selectedTrajectory(records: TrajectoryRecord[], selectedId: string): TrajectoryRecord | undefined {
  return records.find((record) => record.trajectory_id === selectedId) ?? records[0];
}

export function evidenceReferencesForConcept(
  cognitiveState: CognitiveStateRecord,
  conceptId: string,
): string[] {
  const estimate = cognitiveState.concept_estimates.find((entry) => entry.concept_id === conceptId);
  if (!estimate) return [];
  const ids = [
    ...stringValues(estimate.supporting_evidence_ids),
    ...stringValues(estimate.contradictory_evidence_ids),
  ];
  return Array.from(new Set(ids));
}

function stringValues(value: JsonValue | undefined): string[] {
  return Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === "string") : [];
}
