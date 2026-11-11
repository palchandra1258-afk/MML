"""Rule-based diversion outcome and parent-trajectory resumption decisions."""

from __future__ import annotations

from typing import Any, Mapping

from ..cognitive_state.state_schema import validate_cognitive_state
from ..learner_state.state_schema import validate_state as validate_behavioral_state
from ..representation.representation_schema import validate_representation_plan
from .models import RESUMPTION_OUTCOMES
from .validator import validate_context_snapshot, validate_diversion, validate_trajectory

MIN_RESUMPTION_ATTEMPTS = 10
MIN_RESUMPTION_RECENT_ACCURACY = 0.80
MAX_RESUMPTION_WILSON_WIDTH = 0.45


def evaluate_resumption(trajectory: Mapping[str, Any], diversion: Mapping[str, Any],
                        context_snapshot: Mapping[str, Any], *,
                        behavioral_state: Mapping[str, Any] | None = None,
                        cognitive_state: Mapping[str, Any] | None = None,
                        representation_plan: Mapping[str, Any] | None = None,
                        replan_requested: bool = False,
                        completion_requested: bool = False) -> dict[str, Any]:
    validate_trajectory(trajectory)
    validate_diversion(diversion)
    validate_context_snapshot(context_snapshot)
    if trajectory["trajectory_id"] != diversion["parent_trajectory_id"] or trajectory["trajectory_id"] != context_snapshot["parent_trajectory_id"]:
        raise ValueError("resumption inputs do not share the same parent trajectory")
    if trajectory["orchestration"]["active_diversion_id"] != diversion["diversion_id"] or trajectory["current_status"] != "DIVERTED":
        raise ValueError("the supplied diversion is not active on this parent trajectory")
    if diversion["diversion_status"] != "ACTIVE":
        raise ValueError("only an active diversion can be evaluated for resumption")
    if replan_requested and completion_requested:
        raise ValueError("replanning and completion cannot both be requested")
    cognitive_reference = None if cognitive_state is None else {
        "cognitive_state_id": cognitive_state["cognitive_state_id"],
        "state_version": cognitive_state["state_version"],
    }
    if replan_requested:
        return _outcome("REPLAN_PARENT_TRAJECTORY", "explicit_parent_replan", [],
                        "An explicit replan request changes the parent objective; preserved trajectory history remains available.",
                        cognitive_state_reference=cognitive_reference)
    if completion_requested:
        return _outcome("MARK_TRAJECTORY_COMPLETED", "explicit_completion", [],
                        "Completion was explicitly requested. This records a workflow decision, not evidence of mastery.",
                        cognitive_state_reference=cognitive_reference)

    if behavioral_state is not None:
        validate_behavioral_state(behavioral_state)
        if behavioral_state["learner_id"] != diversion["learner_id"]:
            raise ValueError("behavioral state belongs to a different learner")
    if cognitive_state is not None:
        validate_cognitive_state(cognitive_state)
        if cognitive_state["learner_id"] != diversion["learner_id"]:
            raise ValueError("cognitive state belongs to a different learner")
    if behavioral_state is not None and cognitive_state is not None:
        phase9_ref = cognitive_state["observed_evidence_summary"]["phase9_state_reference"]
        if behavioral_state["state_timestamp"] != phase9_ref["state_timestamp"]:
            raise ValueError("Phase 9 and Phase 11 source timestamps do not match")
        phase9_concept = next((item for item in behavioral_state["concept_states"]
                               if item["concept_id"] == diversion["diversion_concept_id"]), None)
        cognitive_concept = next((item for item in cognitive_state["concept_estimates"]
                                  if item["concept_id"] == diversion["diversion_concept_id"]), None)
        if phase9_concept is None or cognitive_concept is None:
            return _outcome("REQUEST_ADDITIONAL_EVIDENCE", "missing_diversion_estimate", [],
                            "The diversion concept is not present in both aligned Phase 9/11 records; keep the diversion and request relevant observations.",
                            cognitive_state_reference=cognitive_reference)
        observed_phase11 = cognitive_concept["observed_performance"]
        for key in ("attempts", "correct", "incorrect", "historical_accuracy", "recent_accuracy",
                    "performance_trend", "performance_change", "uncertainty_interval_95"):
            if phase9_concept[key] != observed_phase11[key]:
                raise ValueError(f"Phase 9 and Phase 11 diversion-concept {key} do not match")
    if representation_plan is not None:
        validate_representation_plan(representation_plan)
        if representation_plan["learner_id"] != diversion["learner_id"]:
            raise ValueError("representation plan belongs to a different learner")
        if representation_plan["concept_id"] != context_snapshot["original_target_concept_id"]:
            raise ValueError("alternative representation plan must target the preserved parent concept")
        if cognitive_state is not None and (
            representation_plan["input_references"]["cognitive_state_id"] != cognitive_state["cognitive_state_id"]
            or representation_plan["input_references"]["cognitive_state_version"] != cognitive_state["state_version"]
        ):
            raise ValueError("representation plan must refer to the supplied cognitive-state version")

    if cognitive_state is not None:
        estimate = next((item for item in cognitive_state["concept_estimates"]
                         if item["concept_id"] == diversion["diversion_concept_id"]), None)
        if estimate is None:
            return _outcome("REQUEST_ADDITIONAL_EVIDENCE", "missing_diversion_estimate", [],
                            "The latest cognitive state has no estimate for the diversion concept; retain the diversion and gather relevant evidence.",
                            cognitive_state_reference=cognitive_reference)
        if estimate["contradictory_evidence_ids"]:
            return _outcome("REQUEST_ADDITIONAL_EVIDENCE", "conflicting_diversion_evidence",
                            estimate["contradictory_evidence_ids"],
                            "Contradictory supporting-concept evidence remains unresolved; do not close or resume on this basis.",
                            cognitive_state_reference=cognitive_reference)
        observed = estimate["observed_performance"]
        sufficiency = estimate["evidence_sufficiency"]
        supporting_ids = list(estimate["supporting_evidence_ids"])
    elif behavioral_state is not None:
        estimate = next((item for item in behavioral_state["concept_states"]
                         if item["concept_id"] == diversion["diversion_concept_id"]), None)
        if estimate is None:
            return _outcome("REQUEST_ADDITIONAL_EVIDENCE", "missing_diversion_estimate", [],
                            "The latest behavioral state has no estimate for the diversion concept; retain the diversion.")
        observed = estimate
        sufficiency = estimate["evidence_sufficiency"]
        supporting_ids = []
    elif diversion["progress_history"]:
        observed = diversion["progress_history"][-1]
        sufficiency = observed["evidence_sufficiency"]
        supporting_ids = observed["evidence_ids"]
    else:
        return _outcome("REQUEST_ADDITIONAL_EVIDENCE", "no_diversion_progress", [],
                        "No diversion progress evidence has been recorded; keep the diversion open and request an observation.",
                        cognitive_state_reference=cognitive_reference)

    attempts = int(observed.get("attempts", 0))
    recent_accuracy = observed.get("recent_accuracy")
    interval = observed.get("uncertainty_interval_95")
    width = interval[1] - interval[0] if interval else None
    if attempts < MIN_RESUMPTION_ATTEMPTS or sufficiency in {"none", "low"} or recent_accuracy is None or width is None:
        return _outcome("REQUEST_ADDITIONAL_EVIDENCE", "insufficient_resumption_evidence", supporting_ids,
                        f"Resumption needs at least {MIN_RESUMPTION_ATTEMPTS} labeled supporting-concept responses and an assessable uncertainty interval; current evidence is insufficient.",
                        cognitive_state_reference=cognitive_reference)
    if (recent_accuracy < MIN_RESUMPTION_RECENT_ACCURACY
            or observed.get("performance_trend") == "declining"
            or width > MAX_RESUMPTION_WILSON_WIDTH):
        return _outcome("CONTINUE_DIVERSION", "supporting_concept_not_yet_stable", supporting_ids,
                        "The supporting-concept evidence has not met the prespecified recent-performance, trend and uncertainty checks; continue the bounded diversion and reassess later.",
                        cognitive_state_reference=cognitive_reference)

    if representation_plan is not None:
        selected = representation_plan["decision"]["selected_representation"]
        available = (selected is not None and representation_plan["decision"]["delivery_status"] == "available")
        previous_id = context_snapshot["previous_representation_plan_id"]
        if available and representation_plan["plan_id"] != previous_id:
            return _outcome("RESUME_WITH_ALTERNATIVE_REPRESENTATION", "supporting_evidence_and_available_alternative",
                            supporting_ids,
                            "Supporting-concept evidence meets the bounded resumption rule and a different executable representation plan is registered for the preserved parent concept.",
                            representation_plan_reference={"plan_id": representation_plan["plan_id"],
                                                           "plan_version": representation_plan["plan_version"],
                                                           "selected_representation": selected,
                                                           "delivery_status": "available"},
                            cognitive_state_reference=cognitive_reference)
    return _outcome("RESUME_ORIGINAL_STEP", "supporting_evidence_meets_resumption_rule", supporting_ids,
                    "Supporting-concept evidence meets the prespecified resumption rule. Return to the exact preserved learning step; this is not a mastery claim.",
                    cognitive_state_reference=cognitive_reference)


def _outcome(outcome: str, rule_id: str, evidence_ids: list[str], explanation: str,
             representation_plan_reference: Mapping[str, Any] | None = None,
             cognitive_state_reference: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if outcome not in RESUMPTION_OUTCOMES:
        raise ValueError(f"unsupported resumption outcome: {outcome}")
    return {
        "outcome": outcome,
        "rule_id": rule_id,
        "supporting_evidence_ids": sorted(set(evidence_ids)),
        "representation_plan_reference": None if representation_plan_reference is None else dict(representation_plan_reference),
        "cognitive_state_reference": None if cognitive_state_reference is None else dict(cognitive_state_reference),
        "explanation": explanation,
        "mastery_claim": False,
    }
