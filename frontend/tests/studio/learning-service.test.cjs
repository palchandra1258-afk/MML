/* eslint-disable @typescript-eslint/no-require-imports */
const assert = require("node:assert/strict");
const test = require("node:test");
const { createLearningService } = require("../../.api-test-dist/lib/services/learning.service.js");

function clientRecording() {
  const calls = [];
  return {
    calls,
    get: async (path, options) => { calls.push({ method: "GET", path, options }); return { data: {}, requestId: "test", status: 200 }; },
    post: async (path, body, options) => { calls.push({ method: "POST", path, body, options }); return { data: {}, requestId: "test", status: 200 }; },
    request: async () => ({ data: {}, requestId: "test", status: 200 }),
  };
}

test("student curriculum service uses the shared API client and encodes topic queries", async () => {
  const client = clientRecording();
  const service = createLearningService(client);
  await service.catalog();
  await service.search("Bayes theorem & probability");
  await service.lesson("conditional-probability");
  assert.deepEqual(client.calls.map((call) => call.path), [
    "/curriculum",
    "/curriculum/search?q=Bayes%20theorem%20%26%20probability",
    "/curriculum/lessons/conditional-probability",
  ]);
  assert.ok(client.calls.every((call) => call.method === "GET"));
});

test("student activity service sends answer and progress writes to backend routes", async () => {
  const client = clientRecording();
  const service = createLearningService(client);
  const answer = { submission_id: "submission-1", session_id: "session-1", response: { option_ids: ["a"] } };
  const progress = { session_id: "session-1", current_section_id: "intro", completed_section_ids: ["intro"] };
  await service.submitAnswer("conditional-probability-q1", answer);
  await service.saveProgress("conditional-probability", progress);
  await service.progress();
  await service.history();
  assert.deepEqual(client.calls.map(({ method, path }) => ({ method, path })), [
    { method: "POST", path: "/studio/questions/conditional-probability-q1/answer" },
    { method: "POST", path: "/studio/lessons/conditional-probability/progress" },
    { method: "GET", path: "/studio/progress" },
    { method: "GET", path: "/studio/history?limit=100" },
  ]);
  assert.deepEqual(client.calls[0].body, answer);
  assert.deepEqual(client.calls[1].body, progress);
});
