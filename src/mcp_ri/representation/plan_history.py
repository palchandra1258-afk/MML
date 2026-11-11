"""Append-only history for versioned RepresentationPlan records."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .representation_schema import validate_representation_plan


def _copy_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(plan), ensure_ascii=False))


class RepresentationPlanHistory:
    """Retain immutable plans for one learner/concept teaching trajectory."""

    def __init__(self, learner_id: str, concept_id: str) -> None:
        if not learner_id or not concept_id:
            raise ValueError("learner_id and concept_id are required")
        self.learner_id = str(learner_id)
        self.concept_id = str(concept_id)
        self._plans: list[dict[str, Any]] = []

    @property
    def plans(self) -> list[dict[str, Any]]:
        return [_copy_plan(plan) for plan in self._plans]

    @property
    def latest(self) -> dict[str, Any] | None:
        return _copy_plan(self._plans[-1]) if self._plans else None

    def append(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        plan = _copy_plan(candidate)
        validate_representation_plan(plan)
        if plan["learner_id"] != self.learner_id or plan["concept_id"] != self.concept_id:
            raise ValueError("plan learner/concept does not match this history")
        if any(item["plan_id"] == plan["plan_id"] for item in self._plans):
            raise ValueError("this representation plan is already present")
        prior = self._plans[-1] if self._plans else None
        expected_version = prior["plan_version"] + 1 if prior else 1
        expected_previous_id = prior["plan_id"] if prior else None
        if plan["plan_version"] != expected_version or plan["previous_plan_id"] != expected_previous_id:
            raise ValueError("plan version and previous_plan_id must continue this history")
        if prior:
            prior_state_version = prior["input_references"]["cognitive_state_version"]
            new_state_version = plan["input_references"]["cognitive_state_version"]
            if new_state_version < prior_state_version:
                raise ValueError("representation plans cannot move to an earlier cognitive-state version")
            for key in (
                "current_concept_id", "current_learning_objective", "current_representation",
                "trajectory_id", "branch_return_pointer",
            ):
                if plan["teaching_context"][key] != prior["teaching_context"][key]:
                    raise ValueError(f"plan history must preserve teaching context field {key}")
            if not set(prior["teaching_context"]["evidence_history_ids"]) <= set(plan["teaching_context"]["evidence_history_ids"]):
                raise ValueError("revised plan must retain earlier evidence history references")
        self._plans.append(plan)
        return _copy_plan(plan)
