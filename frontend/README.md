# MCP-RI Frontend

MCP-RI (Multimodal Cognitive Perception and Representation Intelligence) is a research interface for evidence-linked learner-state estimates, explainable representation plans, and learning-trajectory orchestration. The frontend separates observed response behavior from provisional interpretation, and keeps recommendation availability distinct from actual content delivery.

## Current status

F1–F8 provide the research workspace, shared API integration, representation intelligence, evidence explorer, model evaluation, and production-readiness work. F9 adds a separate Student Learning Studio at `/studio`: curated subject/topic exploration, lesson reading, backend-evaluated practice, persisted progress, and learning history. Student activity uses a fixed, clearly labeled local demo profile isolated from EdNet learner records. Synthetic research walkthrough content remains available only when explicitly enabled with `NEXT_PUBLIC_USE_MOCK_DATA=true`; backend failures never silently fall back to demo records.

The representation route reads learner-scoped saved plans and clearly labeled taxonomy/default-capability source snapshots. The evidence route reads learner-scoped Phase 10 records with embedded group/alignment annotations. The evaluation route displays a versioned, aggregate-only snapshot of allowlisted Phase 6–13 research reports because OpenAPI has no research-report endpoint. It does not read server files in the browser or present report snapshots as live API data. System status reuses the shell’s shared health check. Trajectory and diversion views are read-only; 404 and malformed pagination responses stay explicit errors instead of becoming empty datasets.

The Student Learning Studio serves a small versioned curated catalog with seven complete lessons and objective choice questions plus a numeric expected-value question. Empty AI/ML and Finance catalogs are identified as unavailable. Answer attempts and evidence are append-only and separate from read-only EdNet records; Phase 9 provides an aggregate response-behavior summary with no topic mapping. Cognitive inference, representation delivery, validated prerequisites, authentication, and adaptive trajectory decisions remain unavailable. See [`docs/F9_STUDENT_LEARNING_ENGINE.md`](../docs/F9_STUDENT_LEARNING_ENGINE.md) for the F9 contracts, persistence, setup, and limitations.

## Stack and setup

The project uses Next.js 16.4.6 App Router, React 19.3.0, TypeScript 5, Tailwind CSS 4.3.3, and ESLint 9. No packages were added for F2.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1` and `NEXT_PUBLIC_USE_MOCK_DATA=false` in `.env.local` to use the backend. For an explicitly synthetic walkthrough, set mock mode to `true`; mock mode does not send an API health request. Restart Next.js after changing public environment values. See [`docs/F2_API_INTEGRATION.md`](docs/F2_API_INTEGRATION.md) for backend startup, CORS, and test details.

Available scripts: `dev`, `build`, `start`, `lint`, and `test:api` (built-in Node test runner plus the installed TypeScript compiler).

## Architecture

- `app/`: App Router entry, separate `/studio` student routes, research routes, and shared layout.
- `components/`: application shell, Student Studio lesson/practice screens, learner research views, representation, evidence, research-evaluation and system-status screens, and shared connection/data-state components.
- `lib/api/`: centralized environment config, request/error handling, pagination validation, endpoint paths, and OpenAPI-derived transport types.
- `lib/services/`: health, student curriculum/activity, learner, behavioral state, evidence, cognitive state, representation, and trajectory API methods.
- `hooks/`: shared health state and explicit retry.
- `lib/learner/`: API resource projections, artifact paging, and learner presentation helpers.
- `lib/research/`: typed research artifact catalog and versioned aggregate snapshot with metric provenance.
- `mocks/`: synthetic demonstration scenario, selected only by the explicit mock flag.

The frontend follows the checked-in [`shared/api-contracts/openapi.json`](../shared/api-contracts/openapi.json), not the Python artifact JSON Schemas as HTTP contracts. The Student Studio local demo profile is not authentication and is not suitable for multi-user deployment. See [`docs/F2_API_INTEGRATION.md`](docs/F2_API_INTEGRATION.md) through [`docs/F9_STUDENT_LEARNING_ENGINE.md`](../docs/F9_STUDENT_LEARNING_ENGINE.md) for data sources, provenance, scope, and validation.

## Scientific and product boundaries

EdNet-derived states describe response outcomes and dataset skill tags, not direct understanding or mastery. Cognitive categories are provisional and lack ground truth. All representation delivery capabilities are unavailable by default. The API serves saved research artifacts and limited trajectory operations; an API recommendation does not imply that content was delivered. More details are in [`docs/FRONTEND_LIMITATIONS_AND_ASSUMPTIONS.md`](docs/FRONTEND_LIMITATIONS_AND_ASSUMPTIONS.md).
