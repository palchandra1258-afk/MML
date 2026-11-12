# Error Format

Errors have a stable JSON envelope and never include tracebacks, database URLs, or source paths:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found."
  },
  "timestamp": "2026-11-11T00:00:00.000Z",
  "request_id": "a9f3cba0-87fb-4c91-a6e7-78f7630c7760"
}
```

Validation errors may also include `error.fields`, containing invalid field paths but not submitted values.

| HTTP | Common codes | Meaning |
|---|---|---|
| 404 | `RESOURCE_NOT_FOUND`, `EVIDENCE_NOT_FOUND` | Learner or resource does not exist in the requested scope. |
| 409 | `INVALID_STATE_TRANSITION`, `CONCURRENT_UPDATE`, `RESOURCE_CONFLICT` | Phase 13 transition rejected or stored version conflict. |
| 422 | `INVALID_REQUEST`, `INVALID_REFERENCE`, `INVALID_TRAJECTORY` | Request shape, domain rule, or learner-scoped reference is invalid. |
| 500 | `INTERNAL_ERROR`, `HISTORY_INTEGRITY_ERROR` | Safe generic server error or stored history could not be reconstructed. |
| 503 | `DATABASE_UNAVAILABLE`, `ARTIFACT_INDEX_UNAVAILABLE` | Database or source index is missing/stale. |

Frontend code should branch on both HTTP status and `error.code`. `request_id` is also returned in `X-Request-ID` for support/log correlation.
