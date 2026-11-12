import type { RepresentationRecord } from "../api/types";
import { readString } from "../learner/presentation";

export type PlanFilter = "all" | "selected" | "no-selection" | "additional-evidence" | "diagnostic" | "deferred";

export interface PlanSearchFilters {
  category: PlanFilter;
  planStatus: string;
  query: string;
  selectedRepresentation: string;
  capabilityStatus: string;
  version: string;
  dateFrom: string;
  dateTo: string;
}

export interface PlanPageSummary {
  selected: number;
  noSelection: number;
  additionalEvidence: number;
  diagnostic: number;
  deferred: number;
}

export function matchesPlanFilter(plan: RepresentationRecord, filter: PlanFilter): boolean {
  const action = plan.decision.selected_action;
  switch (filter) {
    case "all": return true;
    case "selected": return plan.decision.selected_representation !== null;
    case "no-selection": return plan.decision.selected_representation === null;
    case "additional-evidence": return action === "request_diagnostic_evidence" || action === "request_additional_evidence";
    case "diagnostic": return plan.plan_kind === "diagnostic" || action === "request_diagnostic_evidence";
    case "deferred": return action === "defer_until_capability_available";
  }
}

export function selectPlanFromPage(plans: RepresentationRecord[], selectedPlanId: string): RepresentationRecord | undefined {
  return plans.find((plan) => plan.plan_id === selectedPlanId) ?? plans[0];
}

/** Counts describe only the records passed in (normally one retrieved page). */
export function summarizePlanRecords(plans: RepresentationRecord[]): PlanPageSummary {
  return {
    selected: plans.filter((plan) => matchesPlanFilter(plan, "selected")).length,
    noSelection: plans.filter((plan) => matchesPlanFilter(plan, "no-selection")).length,
    additionalEvidence: plans.filter((plan) => matchesPlanFilter(plan, "additional-evidence")).length,
    diagnostic: plans.filter((plan) => matchesPlanFilter(plan, "diagnostic")).length,
    deferred: plans.filter((plan) => matchesPlanFilter(plan, "deferred")).length,
  };
}

/** Client-side filtering only. Callers must label the search as page-scoped. */
export function filterPlanRecords(plans: RepresentationRecord[], filters: PlanSearchFilters): RepresentationRecord[] {
  const query = filters.query.trim().toLocaleLowerCase();
  return plans.filter((plan) => {
    if (!matchesPlanFilter(plan, filters.category)) return false;
    if (filters.planStatus !== "all" && plan.decision.delivery_status !== filters.planStatus) return false;
    if (filters.selectedRepresentation === "none" && plan.decision.selected_representation !== null) return false;
    if (filters.selectedRepresentation !== "all" && filters.selectedRepresentation !== "none" && plan.decision.selected_representation !== filters.selectedRepresentation) return false;
    if (filters.capabilityStatus !== "all") {
      const savedStatuses = [
        plan.decision.capability_reference?.status,
        ...plan.decision.alternative_representations.map((item) => item.availability_status),
      ];
      if (!savedStatuses.includes(filters.capabilityStatus)) return false;
    }
    if (filters.version !== "all" && String(plan.plan_version) !== filters.version) return false;
    const createdDate = plan.created_at.slice(0, 10);
    if (filters.dateFrom && createdDate < filters.dateFrom) return false;
    if (filters.dateTo && createdDate > filters.dateTo) return false;
    if (query) {
      // The result set is a single retrieved API page, so searching the saved
      // JSON record stays bounded and includes identifiers, rationale, and
      // source references without inventing a server-side search capability.
      if (!JSON.stringify(plan).toLocaleLowerCase().includes(query)) return false;
    }
    return true;
  });
}

export interface SavedCapabilityObservation {
  representationId: string;
  statuses: string[];
  observedPlanCount: number;
}

/** Collects decision-time status snapshots; it does not represent current availability. */
export function savedCapabilityObservations(plans: RepresentationRecord[]): SavedCapabilityObservation[] {
  const byRepresentation = new Map<string, { statuses: Set<string>; plans: number }>();
  for (const plan of plans) {
    const decision = plan.decision;
    const selectedCapability = decision.capability_reference;
    if (selectedCapability) {
      addObservation(byRepresentation, readString(selectedCapability, "representation_id"), readString(selectedCapability, "status"));
    }
    for (const alternative of decision.alternative_representations) {
      addObservation(byRepresentation, readString(alternative, "representation_id"), readString(alternative, "availability_status"));
    }
  }
  return [...byRepresentation.entries()].map(([representationId, value]) => ({
    representationId,
    statuses: [...value.statuses].sort(),
    observedPlanCount: value.plans,
  }));
}

function addObservation(
  target: Map<string, { statuses: Set<string>; plans: number }>,
  representationId: string | undefined,
  status: string | undefined,
): void {
  if (!representationId) return;
  const entry = target.get(representationId) ?? { statuses: new Set<string>(), plans: 0 };
  entry.statuses.add(status ?? "unknown");
  entry.plans += 1;
  target.set(representationId, entry);
}

