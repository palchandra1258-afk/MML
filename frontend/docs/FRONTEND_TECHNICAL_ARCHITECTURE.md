# Frontend technical architecture

## Existing application baseline

Inspected `frontend/package.json`: Next.js 16.4.6, React/React DOM 19.3.0, TypeScript 5, Tailwind CSS 4.3.3, ESLint 9. App Router starter lives in `app/` (not the proposed `src/app/` layout). There are no chart, icon, query cache, schema validation, or UI component packages installed. Do not migrate to `src/` solely to match a sample tree. Preserve current Next configuration unless a concrete need arises. `frontend/AGENTS.md` requires reading the installed Next docs under `node_modules/next/dist/docs/` before any code implementation; that is an F1 implementation task.

## Proposed structure (incremental, not generated wholesale)

```text
frontend/
  app/
    (learner)/layout.tsx, dashboard/page.tsx, learning/page.tsx, learning-path/...
    (research)/layout.tsx, research/page.tsx, research/learners/[id]/..., evidence/..., evaluation/...
    layout.tsx, page.tsx, globals.css
  components/
    shell/, navigation/, evidence/, status/, visualization/, shared/
  features/
    learner-state/, cognitive-state/, representations/, trajectory/, evidence/, evaluation/
  lib/
    api/client.ts, api/config.ts, api/errors.ts, api/mappers.ts
    format/, accessibility/, constants/
  types/ (domain/view types only when justified)
  mocks/ (explicitly synthetic scenario fixtures, no network/API behavior)
```

Start with shell and the small set of components demanded by reviewed screens; avoid empty folders and generic abstractions. Prefer server components for read-only composition and client components only where browser interaction/state is required. Keep raw API response handling at the server/API boundary. Do not duplicate Python JSON schemas as presumed HTTP response types.

## F2 implementation status

The typed client follows the current Phase 14 OpenAPI 3.1 contract. `lib/api/` owns configuration, GET/POST requests, errors, endpoint paths, and transport types; `lib/services/` mirrors actual backend resources. The shell performs one health check with explicit retry. F3 uses the learner index and read services for behavior, evidence, cognitive estimates, representation plans, and trajectory records. The complete endpoint/type mapping is in [`F2_API_INTEGRATION.md`](F2_API_INTEGRATION.md), with learner screens documented in [`F3_LEARNER_EXPERIENCE.md`](F3_LEARNER_EXPERIENCE.md).

## Data boundaries

Separate three layers: (1) transport types generated/derived only from Phase 14 OpenAPI; (2) frontend view models with learner-friendly labels and formatted timestamps; (3) display components. Mappers must preserve unknown/missing states and provenance. They must not relabel observed correctness as mastery or turn ordinal support tiers into probabilities. Keep source records/version IDs available in researcher views.

## State and caching

Prefer server fetches for initial read-only screens. Adopt client caching only after API interaction patterns, freshness, pagination and mutation invalidation are known. Do not add React Query/SWR or another package preemptively. Mutations need pending/failed/retry feedback and must not optimistically claim state/version changes before persistence acknowledgment. Use URL parameters for researcher filters only after the backend query contract is defined.

## API configuration and failure handling

Centralize base URL lookup in `lib/api/config.ts` using `NEXT_PUBLIC_API_BASE_URL`, validated per environment. Components never assemble backend URLs. API client maps non-2xx responses into typed safe errors, distinguishes unavailable service, authorization (future), validation, not found, and empty result, and includes a request/correlation ID when supplied by the server. Never display stack traces or sensitive payloads. Pagination/loading/error/empty states are part of every list screen.

## Security and roles

Authentication and authorization are not implemented. A role toggle, if used for design demos, is not access control and must be labeled accordingly. Learner data is sensitive; researcher routes need backend-enforced authorization before any real deployment. Avoid logging identifiers or evidence payloads in browser telemetry.

## Testing and quality

F2 adds isolated API client/configuration tests using TypeScript plus Node’s built-in test runner, without new dependencies. Run `npm run test:api`. F9 remains responsible for accessibility, route, journey, responsive, and live-backend checks. Keep lint/build behavior aligned with installed Next 16 docs.
