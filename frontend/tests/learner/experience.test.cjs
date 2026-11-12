const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const test = require("node:test");
const { evidenceForConcept, artifactResourceKey, formatInterval, selectedConcept, selectedTrajectory } = require("../../.api-test-dist/lib/learner/presentation.js");
const { loadLatestIndexedPage } = require("../../.api-test-dist/lib/learner/data.js");
const { nextResourceAttempt, resolveResource } = require("../../.api-test-dist/lib/learner/resource-state.js");
const { navigation } = require("../../.api-test-dist/components/navigation/navigation-data.js");

const page = (items, total, offset = 0, limit = 2) => ({
  data: { items, total, offset, limit, has_more: offset + items.length < total },
  requestId: `request-${offset}`,
  status: 200,
});

test("dashboard resource keys stay idle when a learner artifact is absent", () => {
  assert.equal(artifactResourceKey("L-1", [], "phase9_states"), null);
  assert.equal(artifactResourceKey("L-1", ["phase9_states"], "phase9_states"), "L-1:phase9_states");
});

test("latest indexed page loads the final source-event page and preserves its request ID", async () => {
  const calls = [];
  const result = await loadLatestIndexedPage(async (query) => {
    calls.push(query.offset ?? 0);
    return query.offset ? page(["latest", "last"], 5, 3) : page(["old-1", "old-2"], 5, 0);
  }, 2);
  assert.deepEqual(calls, [0, 3]);
  assert.deepEqual(result.data.items, ["latest", "last"]);
  assert.equal(result.requestId, "request-3");
});

test("latest indexed page handles empty and short responses without inventing rows", async () => {
  const empty = { data: { items: [], total: 0, offset: 0, limit: 4, has_more: false }, requestId: null, status: 200 };
  assert.deepEqual(await loadLatestIndexedPage(async () => empty, 4), empty);
  const noBody = { data: undefined, requestId: null, status: 204 };
  assert.deepEqual(await loadLatestIndexedPage(async () => noBody, 4), noBody);
});

test("concept selection follows the requested ID and falls back to the first returned concept", () => {
  const concepts = [{ concept_id: "skill-a", attempts: 3 }, { concept_id: "skill-b", attempts: 1 }];
  assert.equal(selectedConcept(concepts, "skill-b"), concepts[1]);
  assert.equal(selectedConcept(concepts, "missing"), concepts[0]);
  assert.equal(selectedConcept([], "missing"), undefined);
});

test("concept evidence matches only the source skill tags", () => {
  const records = [
    { evidence_id: "e-1", content: { skill_ids: ["skill-a"] } },
    { evidence_id: "e-2", content: { skill_ids: ["skill-b", "skill-a"] } },
    { evidence_id: "e-3", content: { skill_ids: "skill-a" } },
    { evidence_id: "e-4", content: {} },
  ];
  assert.deepEqual(evidenceForConcept(records, "skill-a").map((record) => record.evidence_id), ["e-1", "e-2"]);
});

test("missing performance intervals remain unavailable instead of becoming zero", () => {
  assert.equal(formatInterval(undefined), "Not reported");
  assert.equal(formatInterval([0, 0.5]), "0%–50%");
});

test("resource state distinguishes missing learner, loading, API error, and successful retry", () => {
  assert.deepEqual(resolveResource(null, 0, null), { status: "idle" });
  assert.deepEqual(resolveResource("L-1:state", 0, null), { status: "loading" });
  const failed = { key: "L-1:state", attempt: 0, status: "error", error: new Error("offline"), requestId: "req-error" };
  const errorState = resolveResource("L-1:state", 0, failed);
  assert.equal(errorState.status, "error");
  assert.equal(errorState.requestId, "req-error");

  const nextAttempt = nextResourceAttempt(0);
  assert.equal(nextAttempt, 1);
  assert.deepEqual(resolveResource("L-1:state", nextAttempt, failed), { status: "loading" });
  assert.deepEqual(resolveResource("L-1:state", nextAttempt, {
    key: "L-1:state", attempt: nextAttempt, status: "success", data: { interactions: 2 }, requestId: "req-ok",
  }), { status: "success", data: { interactions: 2 }, requestId: "req-ok" });
});

test("trajectory selection follows the selected saved ID and safely falls back", () => {
  const records = [{ trajectory_id: "t-1" }, { trajectory_id: "t-2" }];
  assert.equal(selectedTrajectory(records, "t-2"), records[1]);
  assert.equal(selectedTrajectory(records, "missing"), records[0]);
  assert.equal(selectedTrajectory([], "missing"), undefined);
});

test("learner routes remain registered and the shell retains mobile navigation behavior", () => {
  const routes = navigation.flatMap((group) => group.items.map((item) => item.href));
  for (const route of ["/", "/learning", "/progress", "/trajectory", "/learner-state", "/cognitive-state"]) {
    assert.ok(routes.includes(route), `missing navigation route ${route}`);
  }
  const shell = readFileSync(resolve(__dirname, "../../components/layout/app-shell.tsx"), "utf8");
  const styles = readFileSync(resolve(__dirname, "../../app/globals.css"), "utf8");
  assert.match(shell, /mobile-menu-button/);
  assert.match(shell, /aria-expanded=\{mobileOpen\}/);
  assert.match(styles, /@media \(max-width: 850px\)/);
  assert.match(styles, /\.sidebar-wrap--open/);
});
