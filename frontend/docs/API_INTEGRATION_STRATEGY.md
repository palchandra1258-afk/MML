# API integration strategy

## Authority and current state

Phase 14 is a separate backend workstream covering FastAPI, persistence, endpoints, and OpenAPI. No frontend API contract is available here. Python JSON Schemas define artifact shapes, not HTTP routes, pagination, authorization, write semantics, status codes, or response envelopes. Do not invent endpoints or represent the schemas as live transport contracts.

## Integration sequence

1. Obtain the Phase 14 OpenAPI document and agree on base path, versioning, auth, error envelope, pagination, identifiers, and timestamps.
2. Identify read/write operations needed by reviewed journeys and document missing backend capabilities.
3. Generate or derive transport types from the exact OpenAPI version; pin/document generation method. Keep frontend view types separate.
4. Centralize `NEXT_PUBLIC_API_BASE_URL` parsing in a configuration module. Fail clearly in API-enabled environments when missing; allow local fixture mode explicitly.
5. Add a single typed request layer for headers, JSON parsing, abort/timeouts where supported, and error normalization. Components use feature queries/actions, never direct fetch URLs.
6. Map responses to display models without altering scientific meaning; preserve provenance, nulls, unknown fields/enums, versions and references.
7. Implement loading, empty, pagination, retry and stale-data states, then connect each journey end-to-end.

## Candidate resource needs (not endpoint names/contracts)

The journeys need learner/session context; current objective/content; interaction submission and feedback; behavioral state; evidence records/groups/alignments/conflicts; cognitive estimate versions; representation plans and capability registry; trajectory/diversion/context/history; model/evaluation artifacts; and service/artifact health. These are requirements to discuss with Phase 14, not claims that all are implemented or API resources already exist.

## Reliability and caching

Lists need server pagination/filter/sort semantics defined by OpenAPI. Detail references should resolve without fetching giant learner-state exports. Set practical request timeouts, cancellation for route changes, and safe retry only for transient/idempotent reads. Do not retry writes blindly without idempotency semantics. Cache policy depends on update cadence and privacy; use server fetch/revalidation as the initial default, and add a client cache library only if interaction requirements justify it. After successful writes, refetch or invalidate only according to backend version/consistency guarantees.

## Error model and UI

Normalize network offline, timeout, server unavailable, validation, unauthorized/forbidden (once auth exists), not found, rate limit and unknown failures. Show actionable plain-language messages; keep request ID for researcher support where available. Never show stack traces or evidence payloads in generic error UI. Distinguish empty result from failed request and from a record with missing modalities.

## Environment and security

Use `NEXT_PUBLIC_API_BASE_URL` for a browser-consumable public service origin; never put secrets in `NEXT_PUBLIC_*`. Validate HTTPS/deployment origin and CORS with backend owner. Real learner endpoints require backend-enforced access control and privacy review before release. Authentication UI and authorization design are deliberately unimplemented in this plan.

## Mock/API separation

Feature code consumes a repository interface or service function with one explicit mode. Mock fixture selection must be opt-in and watermarked; a backend failure must not silently fall back to synthetic data. Do not combine synthetic and actual records in a chart or table without visible per-record source labels and a clear methodological reason.
