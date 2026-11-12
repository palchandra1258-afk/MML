# F9 Architecture Audit

## Scope and repository state

F9 starts from the existing F1–F8 frontend and Phase 14 FastAPI integration. The initial Git inspection found extensive pre-existing modified and untracked files across the root, frontend, migrations, shared API contract, and backend. Those changes were preserved. This audit was completed before implementation began.

The frontend is Next.js 16.4.6 App Router, React 19, TypeScript, and Tailwind CSS. The backend is FastAPI with Pydantic, SQLAlchemy, Alembic, and SQLite. No additional UI or content dependencies are needed for F9.

## Existing backend capabilities

### Routes and services

The generated OpenAPI contract currently contains:

- `GET /api/v1/health`
- Learner list/detail and saved Phase 9 state, Phase 11 cognitive estimate, Phase 10 evidence, and Phase 12 representation reads.
- Trajectory list/detail/history and diversion reads.
- Trajectory creation and `activate`, `pause`, and `advance_step` actions.

There are no curriculum, lesson, learning-session, answer-attempt, student-progress, or learning-history endpoints. `ResearchService` reads indexed Phase 9–12 JSONL snapshots. `TrajectoryService` is the only application-write service and calls the existing Phase 13 builder/manager before persisting state transitions.

### Persistence

`src/mcp_ri/api/persistence.py` defines SQLAlchemy tables for application metadata, generic learner references, artifact file/record indexes, trajectory snapshots and versions, append-only trajectory history events, diversions, and context snapshots. Alembic revision `0001_initial` creates this schema. There are no tables for curriculum state, student profiles, lesson progress, sessions, or practice attempts.

The API initializes/migrates its configured database at startup. The default local database is `data/application/mcp_ri.sqlite3`; tests use temporary SQLite databases. Any F9 schema change must be additive in a new migration and preserve the current tables and research records.

### Evidence and behavioral state

Phase 10 has a canonical evidence schema, `normalize_evidence`, and an EdNet `InteractionAdapter`. The existing `evidence/state_bridge.py` maps normalized interaction evidence into `LearnerStateAccumulator`. Phase 9 can therefore summarize ordered application responses.

There is an important boundary: the accumulator's `skill_ids()` function prefixes incoming tags with `ednet_skill:`. F9 topic IDs are not validated EdNet skills. Student attempts must not be mapped to those tags. A safe integration can pass an empty skill-ID list and produce an overall response-outcome summary for the separate Student Studio profile; it cannot produce supported topic-level Phase 9 concept states. The source of each new attempt must be recorded as MCP-RI Student Studio, with server-generated event time, question/topic/lesson IDs, content version, and Phase 10 normalized evidence. Those records must remain distinguishable from EdNet records.

### Cognitive, representation, and trajectory integration

- Phase 11 reads saved estimates; it requires a complete matching Phase 9/10 prefix, and the API does not recalculate estimates on demand. No cognitive estimate will be generated from a few new practice answers.
- Phase 12 reads saved recommendation plans. The health contract reports no delivery provider; a plan is not a lesson.
- Phase 13 API mutations require caller-supplied goals and concepts. The current project has no validated curriculum prerequisite graph, no learning-content delivery, and no diversion writes through HTTP. F9 should not invent prerequisites or trigger adaptive diversions. It can keep Student Studio progress separate from research trajectories and describe these limitations.

## Existing frontend capabilities

The application shell supplies the design system, navigation, health indicator, error/loading/empty states, and a shared pseudonymous research-learner selection context. Existing services share one API client and validate the common envelope and pagination response. The selection context is in-memory and cleared on reload; it is not authentication.

The current `/learning` route is a read-only research-record workspace. It explicitly says lessons, quizzes, answer submission, and delivery are unavailable. `/` is the research learner overview. Other routes cover progress, behavioral state, cognitive state, evidence, representations, trajectory, research, evaluation, and system status. There are no Student Studio routes, reusable curriculum/lesson/question models, or student progress/history views.

Existing synthetic data is opt-in and labeled. F9 must not use that research mock as real student activity. Student Studio should have a distinct, explicitly labeled local demo profile and separate UI navigation/workspace; it must never reuse an arbitrary EdNet learner ID.

## API contract and testing conventions

HTTP routes use `/api/v1`, Pydantic schemas, success envelopes with `request_id`, standard error envelopes, request IDs, and CORS configured from `APISettings`. `scripts/api/export_openapi.py` exports the live FastAPI schema to `shared/api-contracts/openapi.json`.

Backend API tests use `TestClient` and per-test temporary SQLite databases in `tests/api/conftest.py`. Frontend checks use the project ESLint/TypeScript configuration and built-in Node test runner. The existing frontend API helpers accept an `ApiClient` dependency, so new service wrappers can follow that pattern.

## F9 architecture decisions

1. Keep a versioned, curated curriculum in structured JSON outside React components. The API validates and serves subjects/topics/lesson blocks. Public lesson/question responses exclude answer keys and scoring specifications.
2. Begin with a small complete probability curriculum, including Conditional Probability, rather than empty catalog entries. Additional subject categories may show honestly unavailable content until complete lessons exist.
3. Give the local Student Studio a fixed explicit demo profile identifier that is separate from all historical research learner IDs. Do not claim login, authentication, or multi-user identity.
4. Add only application-specific progress/session and append-only answer-attempt/evidence persistence using a new Alembic revision. Repeated attempts receive distinct IDs and sequence numbers; an idempotency key prevents an exact retry from duplicating a stored attempt.
5. Evaluate objective question types on the backend. Start with single-choice, multiple-choice, and numeric questions with declared tolerance. Do not claim automated free-text correctness.
6. Derive completion from required lesson sections explicitly marked complete. Derive history, attempt counts, and accuracy from persisted rows. Do not label completion as mastery or a correct answer as durable learning.
7. Normalize persisted attempts into the existing Phase 10 evidence record shape and bridge their outcomes to a separate Phase 9 behavioral summary with no EdNet skill tags. Do not modify historical JSONL files or combine Student Studio records with EdNet evidence indexes.
8. Keep cognitive-state, representation adaptation, validated prerequisites, and Phase 13 diversion/resumption unavailable until their evidence and identity requirements are met.
9. Add an isolated Student Studio route group and workspace navigation while preserving all existing research routes and services.
10. Add backend tests for content secrecy, answer evaluation, validation, idempotency, history, progress, identity isolation, migrations, and evidence/state bridge; add frontend service/projection tests and browser-level end-to-end verification.

## Implementation stages

- **F9.1 — Architecture and data foundation:** schemas, versioned curriculum, additive persistence migration, API contract, and tests.
- **F9.2 — Curriculum and lesson engine:** subjects, topic search/details, lesson retrieval, and curated starter content.
- **F9.3 — Student Learning Studio:** distinct home/explore/lesson routes and workspace switching.
- **F9.4 — Practice and answer evaluation:** server-side choice/numeric evaluation, feedback, idempotent append-only attempts, and normalized evidence.
- **F9.5 — Progress and history:** section checkpoints, resume, derived progress and attempts.
- **F9.6 — MCP-RI integration:** Phase 9 aggregate response summary through the existing bridge; explicitly unsupported cognitive/representation/trajectory inference remains unavailable.
- **F9.7 — End-to-end verification:** backend/frontend checks, browser flow, persistence across reload, OpenAPI export, and final documentation.

## Known limits

There is no authentication provider, multi-user identity, real content-generation service, validated curriculum prerequisite graph, model inference endpoint, or evaluated learning-outcome metric. The initial profile is a local demonstration identity, and access must remain on loopback. The Phase 9 integration is aggregate correctness behavior only; topic-level state, cognitive interpretation, adaptive recommendations, and durable diversion/resumption are out of scope until a validated mapping and complete evidence workflow exist.

## F9 implementation outcome

The completed starter catalog contains seven lessons (five probability, one descriptive statistics, one algorithms) and 15 objective practice questions, including choice and numeric evaluation. Mathematics, Statistics, Computer Science, AI/ML, and Finance are represented; AI/ML and Finance currently have no lesson content. The additive `0002_learning_studio` migration persists local demo profiles, sessions, section checkpoints, append-only attempts, and normalized evidence. The Student Studio and research workspace have distinct navigation and a visible switch.

Verification completed: 28 backend API tests passed; 8 frontend service/API tests passed; frontend ESLint and TypeScript checks passed; the Next.js production build passed. The generated OpenAPI contract was refreshed and matched by the backend contract test. Firefox headless loaded `/studio`, fetched the live catalog and progress, searched for Bayes’ Theorem, and rendered its topic details through the API. The default CORS allowlist now accepts both `localhost:3000` and `127.0.0.1:3000`, matching the documented frontend API URL.
