"""Versioned HTTP routes. Domain rules remain in Phase 13 and service modules."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import API_VERSION
from .dependencies import get_artifact_service, get_research_service, get_session, get_trajectory_service
from .errors import APIError
from .schemas import (
    BehavioralStateRecord,
    CognitiveStateRecord,
    Envelope,
    ErrorEnvelope,
    EvidenceRecord,
    HealthData,
    Identifier,
    LearnerDetail,
    LearnerSummary,
    Page,
    RepresentationRecord,
    TrajectoryActionRequest,
    TrajectoryCreateRequest,
    TrajectoryRecordModel,
)
from .services import ArtifactService, ResearchService, TrajectoryService


router = APIRouter(
    prefix="/api/v1",
    responses={
        404: {"model": ErrorEnvelope, "description": "Requested resource is unavailable."},
        409: {"model": ErrorEnvelope, "description": "State transition or concurrent update conflict."},
        422: {"model": ErrorEnvelope, "description": "Request validation or domain validation error."},
        500: {"model": ErrorEnvelope, "description": "Unexpected server error."},
        503: {"model": ErrorEnvelope, "description": "Database or artifact source is unavailable."},
    },
)


def _request_id(request: Request) -> str:
    return request.state.request_id


def _envelope(request: Request, data: Any) -> dict[str, Any]:
    return {"success": True, "data": data, "request_id": _request_id(request)}


def _page(items: list[Any], total: int, limit: int, offset: int) -> dict[str, Any]:
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "total": total,
        "has_more": offset + len(items) < total,
    }


def _check_learner(service: ResearchService, session: Session, learner_id: str) -> None:
    service.learner_detail(session, learner_id)


@router.get("/health", response_model=Envelope[HealthData], operation_id="getHealth")
def get_health(
    request: Request,
    session: Session = Depends(get_session),
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> dict[str, Any]:
    # Settings are attached by the app factory; fetch through app state to keep DI simple.
    settings = request.app.state.settings
    database_status = "available"
    try:
        session.execute(text("SELECT 1"))
        indexed = artifacts.status(session)
    except SQLAlchemyError:
        database_status = "unavailable"
        indexed = {key: {"available": False, "record_count": 0} for key in settings.artifact_paths()}
    modules = {
        "phase9_behavioral_state": {**indexed["phase9_states"], "mode": "read_only_snapshot_lookup"},
        "phase10_evidence": {**indexed["phase10_evidence"], "mode": "read_only_snapshot_lookup"},
        "phase10_grouping": {**indexed["phase10_groups"], "mode": "read_only_group_and_alignment_annotations"},
        "phase11_cognitive_state": {**indexed["phase11_states"], "mode": "read_only_snapshot_lookup"},
        "phase12_representation": {
            **indexed["phase12_plans"], "mode": "read_only_recommendations", "delivery_provider": False,
        },
        "phase13_trajectory": {"available": database_status == "available", "mode": "durable_application_records"},
        "model_inference": {"available": False, "reason": "No integrated model-loading and inference service is configured."},
    }
    status = "healthy" if database_status == "available" and all(
        indexed[name]["available"] for name in (
            "phase9_states", "phase10_evidence", "phase10_groups", "phase11_states", "phase12_plans",
        )
    ) else "degraded"
    timestamp = datetime.now(timezone.utc).isoformat()
    return _envelope(request, {
        "status": status,
        "api_version": API_VERSION,
        "database": database_status,
        "modules": modules,
        "timestamp": timestamp,
    })


@router.get("/learners", response_model=Envelope[Page[LearnerSummary]], operation_id="listLearners")
def list_learners(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    items, total = service.list_learners(session, limit=limit, offset=offset)
    return _envelope(request, _page(items, total, limit, offset))


@router.get("/learners/{learner_id}", response_model=Envelope[LearnerDetail], operation_id="getLearner")
def get_learner(
    learner_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    return _envelope(request, service.learner_detail(session, learner_id))


@router.get("/learners/{learner_id}/state", response_model=Envelope[BehavioralStateRecord], operation_id="getLearnerState")
def get_learner_state(
    learner_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    _check_learner(service, session, learner_id)
    return _envelope(request, service.behavioral_state(session, learner_id))


@router.get("/learners/{learner_id}/cognitive-state", response_model=Envelope[CognitiveStateRecord], operation_id="getCognitiveState")
def get_cognitive_state(
    learner_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    _check_learner(service, session, learner_id)
    return _envelope(request, service.cognitive_state(session, learner_id))


@router.get("/learners/{learner_id}/evidence", response_model=Envelope[Page[EvidenceRecord]], operation_id="listLearnerEvidence")
def list_evidence(
    learner_id: Identifier,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    evidence_type: str | None = Query(default=None, min_length=1, max_length=80),
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    _check_learner(service, session, learner_id)
    items, total = service.evidence(session, learner_id, limit=limit, offset=offset, evidence_type=evidence_type)
    return _envelope(request, _page(items, total, limit, offset))


@router.get("/learners/{learner_id}/evidence/{evidence_id}", response_model=Envelope[EvidenceRecord], operation_id="getLearnerEvidence")
def get_evidence(
    learner_id: Identifier,
    evidence_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    _check_learner(service, session, learner_id)
    return _envelope(request, service.evidence_record(session, learner_id, evidence_id))


@router.get("/learners/{learner_id}/representations", response_model=Envelope[Page[RepresentationRecord]], operation_id="listRepresentations")
def list_representations(
    learner_id: Identifier,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    _check_learner(service, session, learner_id)
    items, total = service.representations(session, learner_id, limit=limit, offset=offset)
    return _envelope(request, _page(items, total, limit, offset))


@router.get("/learners/{learner_id}/representations/{plan_id}", response_model=Envelope[RepresentationRecord], operation_id="getRepresentation")
def get_representation(
    learner_id: Identifier,
    plan_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: ResearchService = Depends(get_research_service),
) -> dict[str, Any]:
    _check_learner(service, session, learner_id)
    return _envelope(request, service.representation(session, learner_id, plan_id))


@router.get("/learners/{learner_id}/trajectories", response_model=Envelope[Page[TrajectoryRecordModel]], operation_id="listTrajectories")
def list_trajectories(
    learner_id: Identifier,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    research: ResearchService = Depends(get_research_service),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    _check_learner(research, session, learner_id)
    items, total = service.list_trajectories(session, learner_id, limit=limit, offset=offset)
    return _envelope(request, _page(items, total, limit, offset))


@router.get("/learners/{learner_id}/trajectories/{trajectory_id}", response_model=Envelope[TrajectoryRecordModel], operation_id="getTrajectory")
def get_trajectory(
    learner_id: Identifier,
    trajectory_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    return _envelope(request, service.trajectory(session, learner_id, trajectory_id))


@router.get("/learners/{learner_id}/trajectories/{trajectory_id}/history", response_model=Envelope[Page[dict[str, Any]]], operation_id="getTrajectoryHistory")
def get_trajectory_history(
    learner_id: Identifier,
    trajectory_id: Identifier,
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    items, total = service.trajectory_history(session, learner_id, trajectory_id, limit=limit, offset=offset)
    return _envelope(request, _page(items, total, limit, offset))


@router.get("/learners/{learner_id}/diversions", response_model=Envelope[Page[dict[str, Any]]], operation_id="listDiversions")
def list_diversions(
    learner_id: Identifier,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    research: ResearchService = Depends(get_research_service),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    _check_learner(research, session, learner_id)
    items, total = service.list_diversions(session, learner_id, limit=limit, offset=offset)
    return _envelope(request, _page(items, total, limit, offset))


@router.get("/learners/{learner_id}/diversions/{diversion_id}", response_model=Envelope[dict[str, Any]], operation_id="getDiversion")
def get_diversion(
    learner_id: Identifier,
    diversion_id: Identifier,
    request: Request,
    session: Session = Depends(get_session),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    return _envelope(request, service.diversion(session, learner_id, diversion_id))


@router.post("/learners/{learner_id}/trajectories", response_model=Envelope[TrajectoryRecordModel], status_code=201, operation_id="createTrajectory")
def create_trajectory(
    learner_id: Identifier,
    body: TrajectoryCreateRequest,
    request: Request,
    session: Session = Depends(get_session),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    return _envelope(request, service.create_trajectory(session, learner_id, body))


@router.post("/learners/{learner_id}/trajectories/{trajectory_id}/actions", response_model=Envelope[TrajectoryRecordModel], operation_id="applyTrajectoryAction")
def apply_trajectory_action(
    learner_id: Identifier,
    trajectory_id: Identifier,
    body: TrajectoryActionRequest,
    request: Request,
    session: Session = Depends(get_session),
    service: TrajectoryService = Depends(get_trajectory_service),
) -> dict[str, Any]:
    return _envelope(request, service.apply_action(session, learner_id, trajectory_id, body))
