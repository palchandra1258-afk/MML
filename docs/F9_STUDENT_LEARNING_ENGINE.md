# F9 Student Learning Engine

## Product boundary

F9 adds a Student Learning Studio alongside the existing MCP-RI research workspace. Students can browse a versioned curated curriculum, study lesson sections, answer practice questions, and review activity persisted by the backend. Research routes and their read-only EdNet artifact views remain available.

Student Studio uses the fixed `studio-local-demo` profile. It is an explicitly labeled, single local demonstration identity, not authentication or a multi-user account system. Its session, progress, answer attempts, and evidence tables are separate from EdNet learner references and research artifact indexes.

## Curriculum

The authored source is `src/mcp_ri/learning/curriculum.json`, content version `1.0.0`. The API validates its curriculum and lesson/question schemas on first load. It includes seven complete lessons:

- Mathematics: Introduction to Probability, Conditional Probability, Bayes’ Theorem, Random Variables, and Expected Value.
- Statistics: Descriptive Statistics.
- Computer Science: Introduction to Algorithms.
- AI/ML and Finance are listed without lessons and are described as unavailable.

Each lesson has objectives, required sections, definitions, explanations, formulas or worked examples, takeaways, and two or more objective practice questions. A numeric expected-value question exercises the tolerance-based evaluator. All topic prerequisite status is `not_established`; no course completion is presented as mastery. Answer keys, grading rules, and feedback are omitted from public practice responses and only returned after a submission.

## HTTP API

All routes use the `/api/v1` prefix and the standard success/error envelope.

| Route | Purpose |
|---|---|
| `GET /curriculum` | Subject, course, unit, and topic catalog |
| `GET /curriculum/search?q=...` | Search supported topics |
| `GET /curriculum/topics/{topic_id}` | Topic objectives and availability metadata |
| `GET /curriculum/lessons/{lesson_id}` | Structured lesson sections |
| `GET /curriculum/lessons/{lesson_id}/practice` | Public questions without answer keys |
| `GET /studio/profile` | Local demo profile label and notice |
| `POST /studio/lessons/{lesson_id}/sessions` | Create or resume a lesson session |
| `POST /studio/lessons/{lesson_id}/progress` | Save current section and required section checkpoints |
| `POST /studio/questions/{question_id}/answer` | Server-side evaluation and durable attempt creation |
| `GET /studio/progress` | Progress derived from saved sections and attempts |
| `GET /studio/history` | Saved lesson starts and answer attempts |
| `GET /studio/evidence` | Normalized Student Studio evidence records |
| `GET /studio/behavioral-state` | Separate Phase 9 aggregate response summary |

Choice submissions use `{"option_ids":["a"]}`; numeric submissions use `{"value":"2.0"}`. Every request includes a client-generated `submission_id` for idempotent retries. Reusing it with a different answer returns `409`. New submission IDs create distinct append-only attempts with server timestamps and increasing profile event sequence.

## Persistence and progress rules

Alembic revision `0002_learning_studio` adds `studio_profiles`, `studio_learning_sessions`, `studio_lesson_progress`, and `studio_learning_attempts`. It does not rewrite revision `0001`, alter EdNet artifacts, or delete existing tables. Attempts retain the submitted answer, server evaluation, content version, session, sequence, and normalized evidence JSON.

Lesson completion requires every required section to be saved as completed. A recent incorrect attempt can produce `needs_review` while content is incomplete. Once all required sections are completed, status is `completed`. Course completion is the fraction of its curated lessons whose content checkpoints are complete. Accuracy describes recorded responses only. It is not mastery, durable learning, or a validated learning outcome.

## MCP-RI evidence connection

Each evaluated attempt is normalized through the existing Phase 10 evidence builder with `source_dataset="mcp-ri-student-studio"`, a server submission time, content version and activity identifiers. New evidence is replayed in order through `phase9_row_from_interaction` and `apply_interaction_evidence` into a separate aggregate `LearnerStateAccumulator` for `studio-local-demo`. Since Student Studio topics have no validated mapping to EdNet skill IDs, `skill_ids` remains empty and `concept_states` is empty. The API exposes overall counts and response outcomes with those limitations.

F9 does not recalculate Phase 11 estimates, deliver Phase 12 representations, or route Student Studio attempts into Phase 13 research trajectories. No validated prerequisite graph or adaptive decision policy exists for that use. EdNet JSONL artifacts are unchanged.

## Frontend routes and local run

The Student Learning Studio is available at `/studio`, `/studio/explore`, `/studio/subjects/{subjectId}`, `/studio/topics/{topicId}`, `/studio/lessons/{lessonId}`, `/studio/practice/{lessonId}`, `/studio/progress`, and `/studio/history`. The sidebar has an explicit workspace switch; existing learner, evidence, representation, trajectory, research, evaluation, and system-status routes remain in the research workspace.

Run the API from the repository root:

```bash
PYTHONPATH=src .venv-api/bin/uvicorn mcp_ri.api.main:app --host 127.0.0.1 --port 8000
```

Run the frontend with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1` and `NEXT_PUBLIC_USE_MOCK_DATA=false` in `frontend/.env.local`:

```bash
cd frontend
npm run dev
```

The API automatically upgrades its configured SQLite database on startup. By default, CORS allows both `http://localhost:3000` and `http://127.0.0.1:3000`; `MCP_RI_CORS_ORIGINS` can replace that allowlist. Keep the API bound to loopback for this local demo; CORS is not authentication.

## Verification

- Backend: `PYTHONPATH=src .venv-api/bin/pytest tests/api/test_api.py tests/api/test_learning_foundation.py tests/api/test_learning_api.py -q`
- Frontend types and tests: `cd frontend && npm run test:api`
- Frontend lint: `cd frontend && npm run lint`
- Production bundle: `cd frontend && npm run build`
- OpenAPI: `PYTHONPATH=src .venv-api/bin/python scripts/api/export_openapi.py`

The backend API tests use isolated temporary SQLite databases. The configured application database received the additive `0002_learning_studio` migration; existing artifact and trajectory tables were retained. The local demo run must not be treated as an authenticated student service.

## Stage outcomes

| Stage | Delivered contract | Verification |
|---|---|---|
| F9.1 | Strict curriculum/activity schemas and additive `0002_learning_studio` migration | Migration preservation and persisted JSON round-trip tests |
| F9.2 | Versioned content source, five subject categories, topic search, topic details, lesson and public-practice APIs | Catalog shape, prerequisite status, search and answer-key secrecy tests |
| F9.3 | Separate Student Studio home/explore/topic/lesson/progress/history routes and workspace switch | Next.js route build and Firefox homepage/search/topic-detail flow |
| F9.4 | Choice and tolerance-based numeric evaluators, feedback, idempotency and append-only answer evidence | Correct/incorrect, malformed response, replay, new-attempt and numeric tolerance tests |
| F9.5 | Resumable sessions, monotonic required-section checkpoints, derived course progress and history | Session resume, completion, review status and history API tests |
| F9.6 | Phase 10 normalization and isolated Phase 9 aggregate summary with empty skill mapping | Evidence provenance, EdNet separation and no topic-state inference assertions |
| F9.7 | OpenAPI export, frontend/backend docs, local integration and validation | 28 backend tests, 8 frontend tests, lint, TypeScript, production build and browser API checks |
