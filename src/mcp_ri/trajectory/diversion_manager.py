"""Lifecycle operations for bounded LearningDiversion records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from ..cognitive_state.state_schema import validate_cognitive_state
from ..learner_state.state_schema import validate_state as validate_behavioral_state
from .models import SCHEMA_VERSION, copy_record, stable_id
from .validator import validate_context_snapshot, validate_diversion, validate_trajectory


def create_diversion_record(trajectory: Mapping[str, Any], decision: Mapping[str, Any],
                            context_snapshot: Mapping[str, Any], *, now: str) -> dict[str, Any]:
    validate_trajectory(trajectory)
    validate_context_snapshot(context_snapshot)
    dependency = decision.get("dependency")
    if decision.get("action") != "CREATE_DIVERSION" or not dependency:
        raise ValueError("a diversion requires a detector decision with an explicit supporting relationship")
    if context_snapshot["parent_trajectory_id"] != trajectory["trajectory_id"]:
        raise ValueError("context snapshot does not refer to the supplied parent trajectory")
    target = decision.get("target_concept_id")
    if not target or target == trajectory["current_concept_id"]:
        raise ValueError("diversion must have a distinct supporting concept target")
    if not decision.get("supporting_evidence_ids"):
        raise ValueError("diversion requires traceable supporting evidence")
    diversion_id = stable_id("div_", [trajectory["trajectory_id"], target,
                                       trajectory["trajectory_version"], decision["rule_id"]])
    record = {
        "schema_version": SCHEMA_VERSION,
        "diversion_id": diversion_id,
        "learner_id": trajectory["learner_id"],
        "diversion_version": 1,
        "created_at": now,
        "updated_at": now,
        "parent_trajectory_id": trajectory["trajectory_id"],
        "parent_trajectory_version": trajectory["trajectory_version"],
        "parent_concept_id": trajectory["current_concept_id"],
        "parent_learning_objective": trajectory["primary_learning_goal"],
        "diversion_concept_id": target,
        "diversion_skill_ids": [target] if target.startswith("ednet_skill:") else [],
        "diversion_reason": decision["explanation"],
        "supporting_evidence_ids": sorted(set(decision["supporting_evidence_ids"])),
        "cognitive_state_reference": copy_record(decision.get("cognitive_state_reference")),
        "behavioral_state_reference": copy_record(decision.get("behavioral_state_reference")),
        "representation_plan_reference": copy_record(decision.get("representation_plan_reference")),
        "context_snapshot_id": context_snapshot["context_snapshot_id"],
        "previous_learning_step": trajectory["current_learning_step"],
        "previous_representation_plan_id": trajectory["context"]["previous_representation_plan_id"],
        "original_trajectory_status": trajectory["current_status"],
        "resume_condition": "Gather at least 10 labeled supporting-concept responses, then reassess recent accuracy, trend, uncertainty and parent context; this is a review threshold, not proof of mastery.",
        "diversion_status": "ACTIVE",
        "progress_history": [],
        "revision_history": [],
        "evaluation_references": [],
        "created_by_decision_rule": decision["rule_id"],
        "started_at": now,
        "last_evaluated_at": None,
        "resolved_at": None,
        "closure_reason": None,
    }
    validate_diversion(record)
    return record


def update_diversion_progress(diversion: Mapping[str, Any], *,
                              behavioral_state: Mapping[str, Any] | None = None,
                              cognitive_state: Mapping[str, Any] | None = None,
                              evidence_ids: list[str] | None = None,
                              known_evidence_ids: set[str] | None = None,
                              evaluated_at: str | None = None,
                              note: str = "") -> dict[str, Any]:
    validate_diversion(diversion)
    if diversion["diversion_status"] != "ACTIVE":
        raise ValueError("only an active diversion can receive progress updates")
    if behavioral_state is None and cognitive_state is None:
        raise ValueError("progress update requires Phase 9 or Phase 11 evidence")
    if behavioral_state is not None:
        validate_behavioral_state(behavioral_state)
        if behavioral_state["learner_id"] != diversion["learner_id"]:
            raise ValueError("behavioral state belongs to a different learner")
    if cognitive_state is not None:
        validate_cognitive_state(cognitive_state)
        if cognitive_state["learner_id"] != diversion["learner_id"]:
            raise ValueError("cognitive state belongs to a different learner")
    phase9_concept = None
    if behavioral_state is not None:
        phase9_concept = next((item for item in behavioral_state["concept_states"]
                               if item["concept_id"] == diversion["diversion_concept_id"]), None)
    estimate = None
    if cognitive_state is not None:
        estimate = next((item for item in cognitive_state["concept_estimates"]
                         if item["concept_id"] == diversion["diversion_concept_id"]), None)
    if phase9_concept is None and estimate is None:
        raise ValueError("progress evidence must include the diversion concept")
    source_evidence_ids = list(evidence_ids or [])
    if estimate is not None:
        source_evidence_ids.extend(estimate["supporting_evidence_ids"])
    source_evidence_ids = sorted(set(source_evidence_ids))
    if known_evidence_ids is not None and set(source_evidence_ids) - known_evidence_ids:
        raise ValueError("progress update refers to unavailable evidence IDs")
    observed = (phase9_concept if phase9_concept is not None else estimate["observed_performance"])
    cog_ref = None if cognitive_state is None else {
        "cognitive_state_id": cognitive_state["cognitive_state_id"],
        "state_version": cognitive_state["state_version"],
    }
    behavioral_ref = None if behavioral_state is None else {
        "state_timestamp": behavioral_state["state_timestamp"],
        "schema_version": behavioral_state["schema_version"],
    }
    at = evaluated_at or datetime.now(timezone.utc).isoformat()
    progress = {
        "evaluation_key": stable_id("deval_", [cog_ref, behavioral_ref, source_evidence_ids]),
        "evaluated_at": at,
        "attempts": int(observed["attempts"]),
        "correct": int(observed["correct"]),
        "recent_accuracy": observed.get("recent_accuracy", observed.get("recent_accuracy")),
        "performance_trend": observed.get("performance_trend"),
        "evidence_sufficiency": estimate["evidence_sufficiency"] if estimate else observed.get("evidence_sufficiency", "none"),
        "uncertainty_interval_95": observed.get("uncertainty_interval_95"),
        "evidence_ids": source_evidence_ids,
        "cognitive_state_reference": cog_ref,
        "behavioral_state_reference": behavioral_ref,
        "note": note,
    }
    if progress["evaluation_key"] in {item["evaluation_key"] for item in diversion["progress_history"]}:
        return copy_record(diversion)
    updated = copy_record(diversion)
    updated["diversion_version"] += 1
    updated["updated_at"] = at
    updated["last_evaluated_at"] = at
    updated["progress_history"].append(progress)
    updated["evaluation_references"].append({
        "evaluation_key": progress["evaluation_key"], "evidence_ids": source_evidence_ids,
        "cognitive_state_reference": cog_ref, "behavioral_state_reference": behavioral_ref,
    })
    validate_diversion(updated)
    return updated


def close_diversion(diversion: Mapping[str, Any], *, status: str, reason: str,
                    resolved_at: str | None = None) -> dict[str, Any]:
    validate_diversion(diversion)
    if diversion["diversion_status"] != "ACTIVE":
        raise ValueError("diversion is already closed")
    if status not in {"RESOLVED", "CLOSED", "CANCELLED"}:
        raise ValueError("closing status must be RESOLVED, CLOSED or CANCELLED")
    if not reason.strip():
        raise ValueError("closure reason is required")
    at = resolved_at or datetime.now(timezone.utc).isoformat()
    updated = copy_record(diversion)
    updated["diversion_version"] += 1
    updated["updated_at"] = at
    updated["diversion_status"] = status
    updated["resolved_at"] = at
    updated["closure_reason"] = reason.strip()
    validate_diversion(updated)
    return updated
