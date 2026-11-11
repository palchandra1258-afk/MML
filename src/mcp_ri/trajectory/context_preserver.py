"""Capture and restore compact teaching context across temporary diversions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .models import SCHEMA_VERSION, stable_id
from .validator import validate_context_snapshot, validate_trajectory


def create_context_snapshot(trajectory: Mapping[str, Any], *, reason: str,
                            supporting_evidence_ids: list[str],
                            diagnostic_recommendation_ids: list[str] = (),
                            existing_active_diversion_ids: list[str] = (),
                            created_at: str | None = None) -> dict[str, Any]:
    validate_trajectory(trajectory)
    if trajectory["current_status"] not in {"ACTIVE", "PAUSED"}:
        raise ValueError("only an active or paused primary trajectory can be diverted")
    if not reason.strip():
        raise ValueError("a diversion context snapshot requires a reason")
    now = created_at or datetime.now(timezone.utc).isoformat()
    snapshot_id = stable_id("ctx_", [trajectory["trajectory_id"], trajectory["trajectory_version"], reason,
                                     sorted(supporting_evidence_ids), now])
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "context_snapshot_id": snapshot_id,
        "learner_id": trajectory["learner_id"],
        "parent_trajectory_id": trajectory["trajectory_id"],
        "parent_trajectory_version": trajectory["trajectory_version"],
        "captured_at": now,
        "original_target_concept_id": trajectory["target_concept_id"],
        "primary_learning_goal": trajectory["primary_learning_goal"],
        "current_learning_step": trajectory["current_learning_step"],
        "completed_steps": list(trajectory["completed_steps"]),
        "pending_steps": list(trajectory["pending_steps"]),
        "previous_representation_plan_id": trajectory["context"]["previous_representation_plan_id"],
        "previous_cognitive_state_id": trajectory["context"]["previous_cognitive_state_id"],
        "supporting_evidence_ids": sorted(set(
            trajectory["context"]["supporting_evidence_ids"] + supporting_evidence_ids
        )),
        "diagnostic_recommendation_ids": sorted(set(diagnostic_recommendation_ids)),
        "existing_active_diversion_ids": sorted(set(existing_active_diversion_ids)),
        "original_current_depth": trajectory["orchestration"]["current_depth"],
        "original_trajectory_status": trajectory["current_status"],
        "reason_for_diversion": reason.strip(),
    }
    validate_context_snapshot(snapshot)
    return snapshot


def restore_context(trajectory: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    validate_trajectory(trajectory)
    validate_context_snapshot(snapshot)
    if trajectory["trajectory_id"] != snapshot["parent_trajectory_id"]:
        raise ValueError("context snapshot belongs to a different parent trajectory")
    return {
        "target_concept_id": snapshot["original_target_concept_id"],
        "primary_learning_goal": snapshot["primary_learning_goal"],
        "current_learning_step": snapshot["current_learning_step"],
        "completed_steps": list(snapshot["completed_steps"]),
        "pending_steps": list(snapshot["pending_steps"]),
        "previous_representation_plan_id": snapshot["previous_representation_plan_id"],
        "previous_cognitive_state_id": snapshot["previous_cognitive_state_id"],
        "supporting_evidence_ids": list(snapshot["supporting_evidence_ids"]),
        "current_depth": snapshot["original_current_depth"],
        "exact_step_restored": True,
    }
