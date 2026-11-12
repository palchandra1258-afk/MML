"""Creation of versioned primary learning trajectories."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .models import SCHEMA_VERSION, stable_id
from .validator import validate_trajectory


def build_trajectory(learner_id: str, target_concept_id: str, primary_learning_goal: str,
                     *, target_skill_ids: Iterable[str] = (), learning_objectives: Iterable[str] = (),
                     prerequisites: Iterable[str] = (), expected_progression: Iterable[Mapping[str, Any]] = (),
                     previous_representation_plan_id: str | None = None,
                     previous_cognitive_state_id: str | None = None,
                     supporting_evidence_ids: Iterable[str] = (),
                     previous_interventions: Iterable[Mapping[str, Any]] = (),
                     learning_history_reference: str | None = None,
                     trajectory_id: str | None = None, created_at: str | None = None) -> dict[str, Any]:
    if not learner_id or not target_concept_id or not primary_learning_goal.strip():
        raise ValueError("learner_id, target_concept_id and primary_learning_goal are required")
    now = created_at or datetime.now(timezone.utc).isoformat()
    objectives = list(map(str, learning_objectives))
    progression = [dict(step) for step in expected_progression]
    if not progression:
        progression = [{"step_id": f"step:{target_concept_id}:1", "concept_id": target_concept_id,
                        "objective": objectives[0] if objectives else "", "status": "current"}]
    else:
        current = [step for step in progression if step.get("status") == "current"]
        if len(current) != 1:
            raise ValueError("expected_progression must contain exactly one current step")
    current_step = next(step["step_id"] for step in progression if step["status"] == "current")
    completed = [step["step_id"] for step in progression if step["status"] == "completed"]
    pending = [step["step_id"] for step in progression if step["status"] == "pending"]
    identifier = trajectory_id or stable_id("traj_", [learner_id, target_concept_id, primary_learning_goal, now])
    record = {
        "schema_version": SCHEMA_VERSION,
        "trajectory_id": identifier,
        "learner_id": str(learner_id),
        "created_at": now,
        "updated_at": now,
        "trajectory_version": 1,
        "primary_learning_goal": primary_learning_goal.strip(),
        "target_concept_id": str(target_concept_id),
        "target_skill_ids": sorted(set(map(str, target_skill_ids))),
        "learning_objectives": objectives,
        "prerequisites": sorted(set(map(str, prerequisites))),
        "expected_progression": progression,
        "current_concept_id": next(step["concept_id"] for step in progression if step["step_id"] == current_step),
        "current_learning_step": current_step,
        "completed_steps": completed,
        "pending_steps": pending,
        "current_status": "CREATED",
        "context": {
            "previous_representation_plan_id": previous_representation_plan_id,
            "previous_cognitive_state_id": previous_cognitive_state_id,
            "supporting_evidence_ids": sorted(set(map(str, supporting_evidence_ids))),
            "previous_interventions": [dict(item) for item in previous_interventions],
            "learning_history_reference": learning_history_reference,
        },
        "orchestration": {
            "active_diversion_id": None,
            "parent_trajectory_id": None,
            "current_depth": 0,
            "transition_history_reference": f"trajectory-history:{identifier}",
        },
    }
    validate_trajectory(record)
    return record
