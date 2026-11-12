const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const test = require("node:test");
const { navigation, routeContent } = require("../../.api-test-dist/components/navigation/navigation-data.js");

const source = (path) => readFileSync(resolve(__dirname, "../..", path), "utf8");

test("every visible navigation entry maps to a route or the overview root", () => {
  const routes = navigation.flatMap((group) => group.items.map((item) => item.href));
  for (const href of routes) {
    if (href !== "/") assert.ok(routeContent[href.slice(1)], `route metadata missing for ${href}`);
  }
  assert.ok(routes.includes("/research"));
  assert.ok(routes.includes("/evaluation"));
  const route = source("app/[section]/page.tsx");
  assert.match(route, /section === "evaluation" \|\| section === "research"/);
  assert.match(route, /section === "system-status".*SystemStatusPage/);
  assert.match(route, /if \(!content\) notFound\(\)/);
});

test("trajectory exposes saved reference navigation and checks an active diversion by its stored ID", () => {
  const trajectory = source("components/learner/trajectory-page.tsx");
  assert.match(trajectory, /supporting_evidence_ids\.length \? "\/evidence"/);
  assert.match(trajectory, /previous_cognitive_state_id \? "\/cognitive-state"/);
  assert.match(trajectory, /previous_representation_plan_id \? "\/representations"/);
  assert.match(trajectory, /trajectoryService\.getDiversion\(learnerId, activeDiversionId!/);
  assert.match(trajectory, /Referenced active diversion/);
  assert.match(trajectory, /No downstream event is inferred/);
  assert.doesNotMatch(trajectory, /trajectoryService\.(create|applyAction)\(/);
});

test("mock learner views remain isolated and do not fabricate a diversion lifecycle", () => {
  const demo = source("components/learner/demo-learner-section.tsx");
  assert.match(demo, /Synthetic demonstration/);
  assert.match(demo, /contains no real learner record/);
  assert.match(demo, /No synthetic behavioral snapshot is included/);
  assert.match(demo, /No synthetic estimate is included/);
  assert.match(demo, /No demonstration record is available/);
  assert.doesNotMatch(demo, /diversion_status|resume_condition|resumption event/i);
});

test("mobile navigation exposes its state, control relationship, and Escape close behavior", () => {
  const shell = source("components/layout/app-shell.tsx");
  assert.match(shell, /id="primary-navigation"/);
  assert.match(shell, /aria-controls="primary-navigation"/);
  assert.match(shell, /aria-expanded=\{mobileOpen\}/);
  assert.match(shell, /event\.key !== "Escape"/);
  assert.match(shell, /\.mobile-menu-button/);
});

test("shared resource panels preserve 404 and pagination errors as failures rather than empty data", () => {
  const panel = source("components/learner/api-resource-panel.tsx");
  const states = source("components/shared/data-states.tsx");
  assert.match(panel, /status === 404\) return <NotFoundState/);
  assert.match(states, /The requested API resource was not found/);
  const pagination = source("lib/api/pagination.ts");
  assert.match(pagination, /invalid pagination data/);
});

test("system status reuses the shared health result rather than issuing a duplicate request", () => {
  const statusPage = source("components/system/system-status-page.tsx");
  assert.match(statusPage, /useApiHealth\(\)/);
  assert.match(statusPage, /health\.modules/);
  assert.match(statusPage, /Retry health check/);
  assert.doesNotMatch(statusPage, /getHealth\(/);
});
