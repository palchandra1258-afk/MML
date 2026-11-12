# API integration strategy

## Current contract

F2 now follows the checked-in Phase 14 OpenAPI 3.1 contract in `shared/api-contracts/openapi.json` (API version 1.0.0). The live base path is `/api/v1`. Exact routes, response envelopes, CORS, and limitations are documented in [`F2_API_INTEGRATION.md`](F2_API_INTEGRATION.md) and the backend [`API_DESIGN_SPECIFICATION.md`](../../docs/API_DESIGN_SPECIFICATION.md).

Successful responses use `{ success: true, data, request_id }`; failures use a safe error envelope. Lists use `items`, `limit`, `offset`, `total`, and `has_more`. API types are manually derived from OpenAPI and must be reviewed if the JSON contract changes. Artifact JSON remains open-ended where the backend schema preserves the Phase 9–13 payload.

## Implemented client

`lib/api/` centralizes public config, request timeout and cancellation, GET/POST serialization, envelope and error parsing, request IDs, and safe normalized errors. Only current contract methods are implemented. URLs use `NEXT_PUBLIC_API_BASE_URL`; components do not assemble service URLs. Health is queried once when the shell mounts and can be explicitly retried. API failures never trigger mock fallback.

Services mirror actual endpoints under `lib/services/`. No frontend method is added for content delivery, interaction submission, model evaluation, standalone group/conflict resources, diversion writes, or resumption writes because the backend does not expose those operations.

## Configuration and data modes

Copy `.env.example` to `.env.local`. Configure `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_USE_MOCK_DATA`, and optionally `NEXT_PUBLIC_API_TIMEOUT_MS`. Only `NEXT_PUBLIC_USE_MOCK_DATA=true` selects synthetic walkthrough data. Real API mode is selected otherwise and requires a valid URL. No secret belongs in a `NEXT_PUBLIC_*` variable.

## Backend security and CORS

The backend defaults to allowing `http://localhost:3000` and `http://127.0.0.1:3000` with GET/POST/OPTIONS. If the frontend origin changes, configure backend `MCP_RI_CORS_ORIGINS`. The backend has no authentication; do not expose it beyond loopback until access control is implemented. See the F2 integration guide.

## Follow-on integration

F3 connects learner overview, progress, cognitive estimates, representation-plan context, and read-only trajectory/history views to these services. Researcher evidence/representation/evaluation surfaces and any API mutations remain future work. Continue to preserve nulls, provenance, versions, timestamps, uncertainty, and source references. Keep missing/error/empty states distinct. Add additional caching only after API freshness and mutation consistency are agreed. Use `npm run test:api` for API transport and learner projection checks.
