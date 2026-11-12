# Phase 14 Backend Integration Report

## Implemented

- FastAPI application with `/api/v1`, Pydantic request/response models, request IDs, generated docs, CORS configuration, safe error envelopes, and health/module readiness.
- Read-only API integration for Phase 9 behavioral states, Phase 10 evidence plus group/alignment annotations, Phase 11 estimates, and Phase 12 plans.
- SQLite/SQLAlchemy persistence with an Alembic schema, learner references, artifact byte indexes, trajectory current snapshots, immutable versions, append-only events, diversion/context tables, and foreign keys.
- Phase 13-backed trajectory creation, activation, pause, and step advancement. State transitions call `TrajectoryManager`; API routers contain no trajectory business rules.
- Generated OpenAPI JSON and shared API contract documentation.
- Test-only synthetic integration scenarios; no synthetic fixture is served as an actual learner record.
- Indexed the configured validation reports into the local ignored SQLite database: 117,785 behavioral snapshots, 1,000 evidence records, 1,000 groups, 184 cognitive states, and 1,910 representation plans. Actual API smoke requests for learner `u135328` returned 200 across these data endpoints.

## Partially implemented or unavailable

- Diversion and context database tables are present and GET routes are implemented, but HTTP mutations are not exposed. The repository's default dependency registry is empty, and the Phase 14 API does not yet load a reviewed source-backed dependency registry or persist the full diversion/resumption workflow.
- The API returns saved Phase 9–12 results; it does not recompute learner states on demand. Phase 9 requires replaying ordered interactions, and Phase 11 requires a complete matching evidence prefix.
- Authentication is not implemented. Use only the loopback development server or add an identity/access layer before remote deployment.
- Model inference is not implemented; health says unavailable.
- SQLite was exercised. PostgreSQL schema compatibility is designed through SQLAlchemy/Alembic but has not been runtime-tested.
- The required one-time artifact index reads the large validation state file sequentially. It is not run as part of API startup.

## Not changed

The backend implementation did not modify frontend files, Phase 9–13 source schemas, raw EdNet files, the locked-test partition, or experiment result files. Frontend work is present separately in the current working tree. The Phase 13 sample outputs were not imported because their objective text is placeholder-generated.

## Local setup

```bash
python3 -m venv .venv-api
.venv-api/bin/python -m pip install -r requirements-api.txt
PYTHONPATH=src .venv-api/bin/python scripts/api/index_artifacts.py
PYTHONPATH=src .venv-api/bin/python scripts/api/migrate_database.py
PYTHONPATH=src .venv-api/bin/uvicorn mcp_ri.api.main:app --reload --host 127.0.0.1 --port 8000
```

Start the existing Next.js app separately. Configure its `frontend/.env.local` with:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_API_TIMEOUT_MS=10000
```

The timeout is optional and defaults to 10000 ms. CORS permits `http://localhost:3000` and `http://127.0.0.1:3000` by default; set `MCP_RI_CORS_ORIGINS` to a comma-separated allowlist if the frontend uses a different origin. The generated contract is available at `shared/api-contracts/openapi.json`, and the live schema is served at `/api/v1/openapi.json`. The Phase 9 offset index command is a one-time setup for the configured files and can take time because the source file is 2.6 GB.
