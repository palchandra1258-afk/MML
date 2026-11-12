"""FastAPI application factory, middleware and consistent safe error responses."""

from __future__ import annotations

import logging
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import API_VERSION
from .errors import APIError
from .learning_routes import learning_router
from .learning_service import LearningService
from .persistence import Database
from .routers import router
from .services import ArtifactService, ResearchService, TrajectoryService
from .settings import APISettings, REPOSITORY_ROOT


logger = logging.getLogger("mcp_ri.api")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _error(request: Request, status_code: int, code: str, message: str, fields: list[str] | None = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    payload: dict[str, Any] = {
        "success": False,
        "error": {"code": code, "message": message},
        "timestamp": _timestamp(),
        "request_id": request_id,
    }
    if fields:
        payload["error"]["fields"] = fields
    return JSONResponse(status_code=status_code, content=payload)


def _run_migrations(database_url: str) -> None:
    config = Config(str(REPOSITORY_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def create_app(settings: APISettings | None = None, *, migrate_on_start: bool = True) -> FastAPI:
    active_settings = settings or APISettings.from_environment()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        database = Database(active_settings.database_url)
        application.state.database = database
        if migrate_on_start:
            _run_migrations(active_settings.database_url)
            database.ensure_schema_metadata()
        else:
            database.create_schema()
        application.state.artifact_service = ArtifactService(active_settings)
        application.state.research_service = ResearchService(application.state.artifact_service)
        application.state.trajectory_service = TrajectoryService(application.state.artifact_service)
        application.state.learning_service = LearningService()
        try:
            yield
        finally:
            database.dispose()

    application = FastAPI(
        title="MCP-RI Backend API",
        summary="Versioned API for bounded learner research artifacts and durable trajectory records.",
        description=(
            "Research snapshots are served read-only. Trajectory records are application-authored and durable. "
            "Behavioral summaries, cognitive estimates, and representation plans retain their source limitations."
        ),
        version=API_VERSION,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        lifespan=lifespan,
    )
    application.state.settings = active_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        candidate = request.headers.get("X-Request-ID", "")
        request_id = candidate if _REQUEST_ID.fullmatch(candidate) else str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_id=%s method=%s status=%s", request_id, request.method, response.status_code)
        return response

    @application.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        return _error(request, exc.status_code, exc.code, exc.message)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        fields = sorted({".".join(str(part) for part in error.get("loc", ()) if part not in {"body", "query", "path"})
                         for error in exc.errors()})
        fields = [field for field in fields if field]
        return _error(request, 422, "INVALID_REQUEST", "One or more request fields are invalid.", fields)

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        message = "The requested resource was not found." if exc.status_code == 404 else "The request could not be completed."
        return _error(request, exc.status_code, code, message)

    @application.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("Database operation failed for request_id=%s", getattr(request.state, "request_id", "unknown"))
        return _error(request, 503, "DATABASE_UNAVAILABLE", "The database operation could not be completed.")

    @application.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled API error for request_id=%s", getattr(request.state, "request_id", "unknown"))
        return _error(request, 500, "INTERNAL_ERROR", "The server could not complete the request.")

    application.include_router(router)
    application.include_router(learning_router)
    return application


app = create_app()
