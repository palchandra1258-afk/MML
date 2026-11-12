const assert = require("node:assert/strict");
const test = require("node:test");
const { createApiClient } = require("../../.api-test-dist/lib/api/client.js");
const { ApiError } = require("../../.api-test-dist/lib/api/errors.js");
const { resolveApiConfig } = require("../../.api-test-dist/lib/api/config.js");
const { failedConnectionState } = require("../../.api-test-dist/lib/api/connection-state.js");
const { createHealthService, isHealthData } = require("../../.api-test-dist/lib/services/health.service.js");
const { createLearnerService } = require("../../.api-test-dist/lib/services/learner.service.js");

const envelope = (data, requestId = "req-test-1") => ({ success: true, data, request_id: requestId });
const clientWith = (fetchImpl, timeoutMs = 1000) => createApiClient({
  baseUrl: "http://127.0.0.1:8000/api/v1/",
  timeoutMs,
  fetchImpl,
});

test("GET unwraps the API envelope, sends a request ID, and preserves the response ID", async () => {
  let observedUrl;
  let observedInit;
  const client = clientWith(async (url, init) => {
    observedUrl = String(url);
    observedInit = init;
    return new Response(JSON.stringify(envelope({ status: "healthy" })), { status: 200 });
  });
  const result = await client.get("/health");
  assert.equal(observedUrl, "http://127.0.0.1:8000/api/v1/health");
  assert.equal(observedInit.method, "GET");
  assert.match(observedInit.headers.get("X-Request-ID"), /^mcp-ri-/);
  assert.deepEqual(result.data, { status: "healthy" });
  assert.equal(result.requestId, "req-test-1");
});

test("POST serializes a typed JSON request body", async () => {
  const body = { action: "pause", reason: "Review evidence" };
  let observedInit;
  const client = clientWith(async (_url, init) => {
    observedInit = init;
    return new Response(JSON.stringify(envelope({ trajectory_version: 2 })), { status: 200 });
  });
  await client.post("/learners/L1/trajectories/T1/actions", body);
  assert.equal(observedInit.method, "POST");
  assert.equal(observedInit.headers.get("Content-Type"), "application/json");
  assert.deepEqual(JSON.parse(observedInit.body), body);
});

test("network failure becomes a typed network error", async () => {
  const client = clientWith(async () => { throw new TypeError("private low-level details"); });
  await assert.rejects(client.get("/health"), (error) => error instanceof ApiError && error.kind === "network" && !error.message.includes("private"));
});

test("HTTP 4xx preserves the backend error contract safely", async () => {
  const body = { success: false, error: { code: "INVALID_REQUEST", message: "One or more fields are invalid.", fields: ["action"] }, timestamp: "2026-11-11T00:00:00Z", request_id: "req-422" };
  const client = clientWith(async () => new Response(JSON.stringify(body), { status: 422 }));
  await assert.rejects(client.get("/learners/L1"), (error) => error instanceof ApiError && error.kind === "http" && error.status === 422 && error.code === "INVALID_REQUEST" && error.requestId === "req-422" && error.fields[0] === "action");
});

test("HTTP 404 remains a not-found error instead of becoming an empty result", async () => {
  const body = { success: false, error: { code: "NOT_FOUND", message: "The learner record was not found." }, timestamp: "2026-11-11T00:00:00Z", request_id: "req-404" };
  const client = clientWith(async () => new Response(JSON.stringify(body), { status: 404 }));
  await assert.rejects(client.get("/learners/missing"), (error) => error instanceof ApiError && error.status === 404 && error.requestId === "req-404" && error.message.includes("not found"));
});

test("a successful but invalid API envelope is rejected", async () => {
  const client = clientWith(async () => new Response(JSON.stringify({ success: true, result: {} }), { status: 200 }));
  await assert.rejects(client.get("/learners/L1"), (error) => error instanceof ApiError && error.kind === "invalid-envelope");
});

test("HTTP 5xx without an error envelope does not expose response internals", async () => {
  const client = clientWith(async () => new Response("database stack trace", { status: 503 }));
  await assert.rejects(client.get("/health"), (error) => error instanceof ApiError && error.kind === "http" && error.status === 503 && !error.message.includes("stack trace"));
});

test("request timeout aborts the pending request", async () => {
  const client = clientWith((_url, init) => new Promise((_resolve, reject) => {
    init.signal.addEventListener("abort", () => reject(new Error("aborted")), { once: true });
  }), 15);
  await assert.rejects(client.get("/health"), (error) => error instanceof ApiError && error.kind === "timeout");
});

test("invalid JSON from a successful response is a protocol error", async () => {
  const client = clientWith(async () => new Response("not-json", { status: 200, headers: { "Content-Type": "application/json" } }));
  await assert.rejects(client.get("/health"), (error) => error instanceof ApiError && error.kind === "invalid-json");
});

test("empty successful responses are represented without a JSON parse crash", async () => {
  const client = clientWith(async () => new Response(null, { status: 204 }));
  assert.deepEqual(await client.post("/learners/L1/trajectories", {}), { data: undefined, requestId: null, status: 204 });
});

test("health service decodes the real health response", async () => {
  const health = { status: "degraded", api_version: "1.0.0", database: "available", modules: {}, timestamp: "2026-11-11T00:00:00Z" };
  const service = createHealthService(clientWith(async () => new Response(JSON.stringify(envelope(health)), { status: 200 })));
  assert.deepEqual((await service.getHealth()).data, health);
  assert.equal(isHealthData(health), true);
  assert.equal(isHealthData({ status: "healthy" }), false);
});

test("network and timeout errors map to disconnected; HTTP failures map to error", () => {
  assert.equal(failedConnectionState(new ApiError("offline", { kind: "network" })), "disconnected");
  assert.equal(failedConnectionState(new ApiError("timeout", { kind: "timeout" })), "disconnected");
  assert.equal(failedConnectionState(new ApiError("unhealthy", { kind: "http", status: 503 })), "error");
});

test("mock and real API modes require explicit configuration", () => {
  const mock = resolveApiConfig({ useMockData: "true", nodeEnvironment: "development" });
  assert.equal(mock.mode, "mock");
  assert.equal(mock.baseUrl, null);
  const real = resolveApiConfig({ useMockData: "false", apiBaseUrl: "http://127.0.0.1:8000/api/v1", nodeEnvironment: "development" });
  assert.equal(real.mode, "api");
  assert.equal(real.configurationError, undefined);
  assert.equal(resolveApiConfig({ useMockData: "truee" }).configurationError.kind, "invalid");
});

test("learner service propagates API failure and does not fall back to demo data", async () => {
  const service = createLearnerService(clientWith(async () => { throw new TypeError("offline"); }));
  await assert.rejects(service.list(), (error) => error instanceof ApiError && error.kind === "network");
});
