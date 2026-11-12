"""FastAPI dependencies for request-scoped database sessions and services."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from .persistence import Database
from .services import ArtifactService, ResearchService, TrajectoryService
from .learning_service import LearningService


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.database.session()
    try:
        yield session
    finally:
        session.close()


def get_artifact_service(request: Request) -> ArtifactService:
    return request.app.state.artifact_service


def get_research_service(request: Request) -> ResearchService:
    return request.app.state.research_service


def get_trajectory_service(request: Request) -> TrajectoryService:
    return request.app.state.trajectory_service


def get_learning_service(request: Request) -> LearningService:
    return request.app.state.learning_service
