const assert = require("node:assert/strict");
const test = require("node:test");
const { ApiError } = require("../../.api-test-dist/lib/api/errors.js");
const { isApiPage, validateApiPage } = require("../../.api-test-dist/lib/api/pagination.js");
const { createLearnerService } = require("../../.api-test-dist/lib/services/learner.service.js");
const { createApiClient } = require("../../.api-test-dist/lib/api/client.js");

const page = { items: [{ learner_id: "L-1", available_data: [] }], limit: 20, offset: 0, total: 1, has_more: false };
const result = (data) => ({ data, requestId: "req-page", status: 200 });
const clientWith = (data) => createApiClient({
  baseUrl: "http://127.0.0.1:8000/api/v1",
  timeoutMs: 1000,
  fetchImpl: async () => new Response(JSON.stringify({ success: true, data, request_id: "req-page" }), { status: 200 }),
});

test("API page validation accepts complete, empty, and beyond-end pagination responses", () => {
  assert.equal(isApiPage(page), true);
  assert.equal(isApiPage({ items: [], limit: 20, offset: 40, total: 3, has_more: false }), true);
  assert.deepEqual(validateApiPage(result(page)).data, page);
});

test("API page validation rejects malformed metadata and unsafe item arrays", () => {
  for (const invalid of [
    { ...page, items: "not a list" },
    { ...page, limit: 0 },
    { ...page, offset: -1 },
    { ...page, total: -1 },
    { ...page, has_more: "false" },
    { ...page, total: 3, has_more: false },
    { ...page, items: [{ learner_id: "L1" }, { learner_id: "L2" }], limit: 1, total: 2 },
    { ...page, items: [null] },
  ]) {
    assert.equal(isApiPage(invalid), false);
    assert.throws(() => validateApiPage(result(invalid)), (error) => error instanceof ApiError && error.kind === "invalid-envelope" && error.requestId === "req-page");
  }
});

test("learner list service rejects malformed pagination before UI consumption", async () => {
  const service = createLearnerService(clientWith({ items: {}, limit: 20, offset: 0, total: 0, has_more: false }));
  await assert.rejects(service.list(), (error) => error instanceof ApiError && error.kind === "invalid-envelope");
});
