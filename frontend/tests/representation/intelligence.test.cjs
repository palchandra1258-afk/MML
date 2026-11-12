const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const test = require("node:test");
const { representationTaxonomy, defaultCapabilityRegistry, taxonomyVersion } = require("../../.api-test-dist/lib/representation/catalog.js");
const { filterPlanRecords, matchesPlanFilter, savedCapabilityObservations, selectPlanFromPage, summarizePlanRecords } = require("../../.api-test-dist/lib/representation/plan-analysis.js");
const { createRepresentationService } = require("../../.api-test-dist/lib/services/representation.service.js");

function plan(overrides = {}) {
  return {
    learner_id: "L-1",
    schema_version: "1.0",
    taxonomy_version: "1.0",
    plan_id: "P-1",
    concept_id: "skill-a",
    created_at: "2026-11-01T10:00:00Z",
    plan_version: 1,
    previous_plan_id: null,
    plan_kind: "standard",
    input_references: { supporting_evidence_ids: ["E-support"], contradictory_evidence_ids: ["E-conflict"], cognitive_state_id: "C-1", cognitive_state_version: 2 },
    teaching_context: {},
    concept_grounding: {},
    decision: {
      selected_representation: "visual",
      selected_action: "select_representation",
      delivery_status: "not_selected",
      capability_reference: { representation_id: "visual", status: "available", provider_id: "provider-a", content_ids: ["content-a"] },
      decision_reason: "A visual explanation was selected for the concept.",
      decision_method: "rule_based",
      decision_confidence: "low",
      confidence_scope: "decision_support_only",
      policy_trace: [],
      alternative_representations: [{ representation_id: "textual", availability_status: "unavailable", selection_status: "not_selected", reason: "No content source" }],
    },
    learning_objective: {},
    representation_configuration: {},
    evaluation_strategy: [],
    limitations: {},
    ...overrides,
  };
}

const baseFilters = {
  category: "all",
  planStatus: "all",
  query: "",
  selectedRepresentation: "all",
  capabilityStatus: "all",
  version: "all",
  dateFrom: "",
  dateTo: "",
};

test("taxonomy snapshot contains versioned backend types with unique identifiers", () => {
  assert.equal(taxonomyVersion, "1.0");
  assert.deepEqual(representationTaxonomy.map((item) => item.representation_id), [
    "textual", "worked_example", "visual", "symbolic", "interactive", "simulation", "diagnostic", "alternative_explanation",
  ]);
  assert.equal(new Set(representationTaxonomy.map((item) => item.representation_id)).size, representationTaxonomy.length);
  for (const item of representationTaxonomy) {
    assert.ok(item.label);
    assert.ok(Array.isArray(item.examples));
    assert.ok(Array.isArray(item.configuration_fields));
  }
});

test("default capability snapshot matches taxonomy and does not claim executable delivery", () => {
  assert.deepEqual(defaultCapabilityRegistry.map((item) => item.representation_id), representationTaxonomy.map((item) => item.representation_id));
  assert.ok(defaultCapabilityRegistry.every((item) => item.status === "unavailable"));
  assert.ok(defaultCapabilityRegistry.every((item) => item.provider_id === null && item.content_ids.length === 0));
});

test("plan selection uses the chosen record and falls back to the first retrieved item", () => {
  const plans = [plan(), plan({ plan_id: "P-2" })];
  assert.equal(selectPlanFromPage(plans, "P-2"), plans[1]);
  assert.equal(selectPlanFromPage(plans, "missing"), plans[0]);
  assert.equal(selectPlanFromPage([], "missing"), undefined);
});

test("plan categories retain overlapping saved decision classifications", () => {
  const selected = plan();
  const diagnostic = plan({ plan_id: "P-2", plan_kind: "diagnostic", decision: { ...plan().decision, selected_representation: null, selected_action: "request_diagnostic_evidence", delivery_status: "not_selected" } });
  const deferred = plan({ plan_id: "P-3", decision: { ...plan().decision, selected_representation: null, selected_action: "defer_until_capability_available", delivery_status: "deferred" } });
  assert.equal(matchesPlanFilter(selected, "selected"), true);
  assert.equal(matchesPlanFilter(diagnostic, "no-selection"), true);
  assert.equal(matchesPlanFilter(diagnostic, "additional-evidence"), true);
  assert.equal(matchesPlanFilter(diagnostic, "diagnostic"), true);
  assert.equal(matchesPlanFilter(deferred, "deferred"), true);
  assert.deepEqual(summarizePlanRecords([selected, diagnostic, deferred]), { selected: 1, noSelection: 2, additionalEvidence: 1, diagnostic: 1, deferred: 1 });
});

test("research filters search retrieved page fields and apply status, capability, version, and date constraints", () => {
  const first = plan();
  const second = plan({
    learner_id: "L-2",
    plan_id: "P-2",
    concept_id: "skill-b",
    created_at: "2026-11-08T10:00:00Z",
    plan_version: 3,
    input_references: { supporting_evidence_ids: ["E-other"], contradictory_evidence_ids: [], cognitive_state_id: "C-2", cognitive_state_version: 1 },
    decision: { ...first.decision, selected_representation: null, selected_action: "request_additional_evidence", delivery_status: "deferred", capability_reference: null, alternative_representations: [{ representation_id: "visual", availability_status: "unavailable", selection_status: "rejected", reason: "Provider missing" }], decision_reason: "Additional evidence required." },
  });
  assert.deepEqual(filterPlanRecords([first, second], { ...baseFilters, query: "E-conflict" }), [first]);
  assert.deepEqual(filterPlanRecords([first, second], { ...baseFilters, query: "L-2", planStatus: "deferred" }), [second]);
  assert.deepEqual(filterPlanRecords([first, second], { ...baseFilters, selectedRepresentation: "visual", capabilityStatus: "available", version: "1", dateFrom: "2026-11-01", dateTo: "2026-11-03" }), [first]);
  assert.deepEqual(filterPlanRecords([first, second], { ...baseFilters, category: "additional-evidence", capabilityStatus: "unavailable", version: "3", dateFrom: "2026-11-07" }), [second]);
  assert.deepEqual(filterPlanRecords([first], { ...baseFilters, query: "P-2" }), []);
  assert.deepEqual(filterPlanRecords([], baseFilters), []);
});

test("saved capability observations remain identified as plan-time snapshots", () => {
  const plans = [plan(), plan({ plan_id: "P-2", decision: { ...plan().decision, alternative_representations: [{ representation_id: "textual", availability_status: "unavailable" }] } })];
  const observations = savedCapabilityObservations(plans);
  assert.deepEqual(observations.find((item) => item.representationId === "textual"), { representationId: "textual", statuses: ["unavailable"], observedPlanCount: 2 });
  assert.deepEqual(observations.find((item) => item.representationId === "visual"), { representationId: "visual", statuses: ["available"], observedPlanCount: 2 });
});

test("representation service reads paginated list and plan detail through the shared API client", async () => {
  const calls = [];
  const client = { get: async (path, options) => { calls.push({ path, options }); return { data: { items: [], total: 0, limit: 10, offset: 20, has_more: false }, requestId: "req-f4", status: 200 }; } };
  const service = createRepresentationService(client);
  await service.list("L-1", { limit: 10, offset: 20 });
  await service.get("L-1", "P-1");
  assert.equal(calls[0].path, "/learners/L-1/representations?limit=10&offset=20");
  assert.equal(calls[1].path, "/learners/L-1/representations/P-1");
  assert.equal(calls[0].options.signal, undefined);
});

test("representation page exposes accessible selection, filtering, comparison, and honest empty and source states", () => {
  const page = readFileSync(resolve(__dirname, "../../components/representation/representation-intelligence-page.tsx"), "utf8");
  const detail = readFileSync(resolve(__dirname, "../../components/representation/representation-plan-detail.tsx"), "utf8");
  const styles = readFileSync(resolve(__dirname, "../../app/globals.css"), "utf8");
  assert.match(page, /aria-pressed=\{selectedId === item\.representation_id\}/);
  assert.match(page, /type="search"/);
  assert.match(page, /type="date"/);
  assert.match(page, /Reset filters/);
  assert.match(page, /<PlanComparison plans=\{comparisonPlans\}/);
  assert.match(page, /No plans match these filters/);
  assert.match(page, /Repository snapshot/);
  assert.match(page, /execution not established/);
  assert.doesNotMatch(page, />Executed</);
  assert.match(detail, /representationService\.get/);
  assert.match(detail, /decision\.decision_reason/);
  assert.match(detail, /evidenceService\.get/);
  assert.match(detail, /href="\/evidence"/);
  assert.match(detail, /href="\/cognitive-state"/);
  assert.match(detail, /Validation result not exposed/);
  assert.match(styles, /@media \(max-width: 680px\)/);
  assert.match(styles, /\.representation-plan-filters/);
  assert.match(styles, /\.representation-comparison-table-wrap/);
});
