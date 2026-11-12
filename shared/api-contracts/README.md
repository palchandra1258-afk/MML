# MCP-RI Shared API Contracts

These files define the Phase 14 frontend integration boundary. They describe only the running FastAPI routes and their Pydantic models; the frontend does not need to import Python modules.

- [`openapi.json`](openapi.json) is generated from `mcp_ri.api.main:app`.
- [`API_ENDPOINTS.md`](API_ENDPOINTS.md) describes paths, methods, query parameters, writes, and availability behavior.
- [`DATA_MODELS.md`](DATA_MODELS.md) explains envelopes and source-domain records.
- [`ERROR_FORMAT.md`](ERROR_FORMAT.md) defines common errors and HTTP codes.

Regenerate OpenAPI after route/schema changes with:

```bash
PYTHONPATH=src .venv-api/bin/python scripts/api/export_openapi.py
```

Local base URL: `http://127.0.0.1:8000/api/v1`. CORS defaults to `http://localhost:3000`.
