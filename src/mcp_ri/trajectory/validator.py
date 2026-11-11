"""Schema and cross-record checks for Phase 13 objects."""

from __future__ import annotations

from typing import Any, Mapping

from .models import TRAJECTORY_STATES
from .schemas import CONTEXT_SCHEMA, DIVERSION_SCHEMA, TRAJECTORY_SCHEMA, validate_document


def validate_trajectory(trajectory: Mapping[str, Any]) -> None:
    validate_document(trajectory, TRAJECTORY_SCHEMA, "learning trajectory")
    if trajectory["current_status"] not in TRAJECTORY_STATES:
        raise ValueError("unknown trajectory state")
    steps = trajectory["expected_progression"]
    step_ids = [step["step_id"] for step in steps]
    if len(step_ids) != len(set(step_ids)):
        raise ValueError("expected_progression step IDs must be unique")
    if trajectory["current_learning_step"] not in step_ids:
        raise ValueError("current_learning_step must refer to expected_progression")
    if len([step for step in steps if step["status"] == "current"]) > 1:
        raise ValueError("at most one progression step can be current")
    completed = set(trajectory["completed_steps"])
    pending = set(trajectory["pending_steps"])
    if completed & pending or (completed | pending) - set(step_ids):
        raise ValueError("completed_steps and pending_steps must be disjoint known steps")
    if trajectory["orchestration"]["active_diversion_id"] is None and trajectory["current_status"] == "DIVERTED":
        raise ValueError("DIVERTED trajectory requires active_diversion_id")
    if trajectory["current_status"] == "DIVERTED" and trajectory["orchestration"]["current_depth"] < 1:
        raise ValueError("DIVERTED trajectory depth must be positive")


def validate_diversion(diversion: Mapping[str, Any]) -> None:
    validate_document(diversion, DIVERSION_SCHEMA, "learning diversion")
    if diversion["diversion_status"] == "ACTIVE" and diversion["resolved_at"] is not None:
        raise ValueError("active diversion cannot have resolved_at")
    if diversion["diversion_status"] in {"RESOLVED", "CLOSED", "CANCELLED"}:
        if diversion["resolved_at"] is None or not diversion["closure_reason"]:
            raise ValueError("closed diversion requires resolved_at and closure_reason")


def validate_context_snapshot(snapshot: Mapping[str, Any]) -> None:
    validate_document(snapshot, CONTEXT_SCHEMA, "trajectory context snapshot")
