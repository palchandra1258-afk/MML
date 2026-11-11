"""Conservative, inspectable rules for temporary learning diversions."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..cognitive_state.state_schema import validate_cognitive_state
from ..evidence.evidence_schema import validate_evidence
from ..learner_state.state_schema import validate_state as validate_behavioral_state
from ..representation.representation_schema import validate_representation_plan
from .dependency_registry import ConceptDependencyRegistry
from .validator import validate_trajectory

MIN_PATTERN_ATTEMPTS = 5


def _performance(trajectory: Mapping[str, Any], behavioral_state: Mapping[str, Any] | None,
                 cognitive_state: Mapping[str, Any] | None) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    concept_id = trajectory["current_concept_id"]
    if behavioral_state is not None:
        item = next((c for c in behavioral_state["concept_states"] if c["concept_id"] == concept_id), None)
        if item:
            ids: list[str] = []
            if cognitive_state is not None:
                estimate = next((c for c in cognitive_state["concept_estimates"] if c["concept_id"] == concept_id), None)
                if estimate:
                    ids = list(estimate["supporting_evidence_ids"])
            return dict(item), ids, list(item.get("potential_issues", []))
    if cognitive_state is not None:
        estimate = next((c for c in cognitive_state["concept_estimates"] if c["concept_id"] == concept_id), None)
        if estimate:
            observed = estimate["observed_performance"]
            derived = {
                **observed,
                "evidence_sufficiency": estimate["evidence_sufficiency"],
                "estimate_confidence": "low",
                "potential_issues": list(observed.get("potential_issues", [])),
            }
            issues = list(derived["potential_issues"])
            return derived, list(estimate["supporting_evidence_ids"]), issues
    return None, [], []


def detect_diversion(trajectory: Mapping[str, Any], *,
                     behavioral_state: Mapping[str, Any] | None = None,
                     cognitive_state: Mapping[str, Any] | None = None,
                     evidence_records: Sequence[Mapping[str, Any]] = (),
                     representation_plan: Mapping[str, Any] | None = None,
                     dependency_registry: ConceptDependencyRegistry | None = None,
                     allow_synthetic_dependencies: bool = False) -> dict[str, Any]:
    """Return a deterministic decision; never asserts that a prerequisite is lacking.

    The detector can recommend a temporary diagnostic review only when a
    configured supporting relationship exists and current-concept evidence is
    sufficiently traceable. Without that relationship it asks for evidence and
    leaves the primary trajectory untouched.
    """
    validate_trajectory(trajectory)
    learner_id = trajectory["learner_id"]
    if behavioral_state is not None:
        validate_behavioral_state(behavioral_state)
        if behavioral_state["learner_id"] != learner_id:
            raise ValueError("behavioral state belongs to a different learner")
    if cognitive_state is not None:
        validate_cognitive_state(cognitive_state)
        if cognitive_state["learner_id"] != learner_id:
            raise ValueError("cognitive state belongs to a different learner")
    if behavioral_state is None and cognitive_state is None:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "insufficient_state_inputs", None, [],
                         "No Phase 9 or Phase 11 state was supplied; preserve the primary trajectory and request evidence.")

    if behavioral_state is not None and cognitive_state is not None:
        ref = cognitive_state["observed_evidence_summary"]["phase9_state_reference"]
        if behavioral_state["state_timestamp"] != ref["state_timestamp"]:
            raise ValueError("Phase 9 and Phase 11 source timestamps do not match")
        behavioral_concept = next((item for item in behavioral_state["concept_states"]
                                   if item["concept_id"] == trajectory["current_concept_id"]), None)
        cognitive_concept = next((item for item in cognitive_state["concept_estimates"]
                                  if item["concept_id"] == trajectory["current_concept_id"]), None)
        if cognitive_concept is not None:
            if behavioral_concept is None:
                raise ValueError("Phase 9 source state lacks the Phase 11 current concept")
            observed = cognitive_concept["observed_performance"]
            for phase9_key, cognitive_key in (
                ("attempts", "attempts"), ("correct", "correct"), ("incorrect", "incorrect"),
                ("historical_accuracy", "historical_accuracy"), ("recent_accuracy", "recent_accuracy"),
                ("performance_trend", "performance_trend"), ("performance_change", "performance_change"),
                ("uncertainty_interval_95", "uncertainty_interval_95"),
            ):
                if behavioral_concept[phase9_key] != observed[cognitive_key]:
                    raise ValueError(f"Phase 9 and Phase 11 current-concept {phase9_key} do not match")
    evidence_ids: set[str] = set()
    if cognitive_state is not None:
        evidence_ids = {item["evidence_id"] for item in cognitive_state["evidence_references"]}
        for record in evidence_records:
            validate_evidence(record)
            if record["learner_id"] != learner_id or record["evidence_id"] not in evidence_ids:
                raise ValueError("Phase 10 evidence must belong to and be referenced by the supplied cognitive state")
    if representation_plan is not None:
        validate_representation_plan(representation_plan)
        if representation_plan["learner_id"] != learner_id or representation_plan["concept_id"] != trajectory["current_concept_id"]:
            raise ValueError("representation plan must match the current learner and concept")
        if cognitive_state is not None and representation_plan["input_references"]["cognitive_state_id"] != cognitive_state["cognitive_state_id"]:
            raise ValueError("representation plan must refer to the supplied cognitive state")
        if cognitive_state is not None and representation_plan["input_references"]["cognitive_state_version"] != cognitive_state["state_version"]:
            raise ValueError("representation plan cognitive-state version does not match the supplied state")

    source_reference = None
    if cognitive_state is not None:
        source_reference = {"cognitive_state_id": cognitive_state["cognitive_state_id"],
                            "state_version": cognitive_state["state_version"]}
    behavioral_reference = None
    if behavioral_state is not None:
        behavioral_reference = {"schema_version": behavioral_state["schema_version"],
                                "state_timestamp": behavioral_state["state_timestamp"]}
    plan_reference = None if representation_plan is None else {
        "plan_id": representation_plan["plan_id"], "plan_version": representation_plan["plan_version"],
        "selected_representation": representation_plan["decision"]["selected_representation"],
        "delivery_status": representation_plan["decision"]["delivery_status"],
    }
    estimate = None
    if cognitive_state is not None:
        estimate = next((item for item in cognitive_state["concept_estimates"]
                         if item["concept_id"] == trajectory["current_concept_id"]), None)
        summary = cognitive_state["observed_evidence_summary"]
        if (estimate and estimate["contradictory_evidence_ids"]) or summary["contradictory_evidence_count"]:
            refs = estimate["contradictory_evidence_ids"] if estimate else summary["contradictory_evidence_ids"]
            return _decision("REQUEST_ADDITIONAL_EVIDENCE", "conflicting_evidence", None, refs,
                             "Contradictory evidence is preserved. Do not divert based on a conflict; request clarification or diagnostic evidence.",
                             source_reference, behavioral_reference, plan_reference)

    if representation_plan is not None:
        decision = representation_plan["decision"]
        if decision["selected_representation"] is None and decision["selected_action"] == "defer_until_capability_available":
            return _decision("CONTINUE_PRIMARY", "representation_capability_unavailable", None, [],
                             "The plan is deferred because delivery capability is unavailable. That is not evidence of a knowledge gap, so retain the current learning context.",
                             source_reference, behavioral_reference, plan_reference)

    stats, concept_evidence_ids, issues = _performance(trajectory, behavioral_state, cognitive_state)
    if stats is None:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "missing_current_concept_estimate", None, [],
                         "No performance estimate is available for the current concept; preserve the primary trajectory.",
                         source_reference, behavioral_reference, plan_reference)
    attempts = int(stats.get("attempts", 0))
    sufficiency = stats.get("evidence_sufficiency", "none")
    if attempts < MIN_PATTERN_ATTEMPTS or sufficiency in {"none", "low"}:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "insufficient_current_concept_evidence", None,
                         concept_evidence_ids,
                         f"Only {attempts} current-concept attempts with {sufficiency} evidence sufficiency are available; preserve the primary trajectory and gather more evidence.",
                         source_reference, behavioral_reference, plan_reference)
    if "inconsistent_recent_responses" in issues:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "inconsistent_evidence", None,
                         concept_evidence_ids,
                         "Recent responses are inconsistent. Request a diagnostic observation before considering a diversion.",
                         source_reference, behavioral_reference, plan_reference)

    triggers = []
    if "repeated_recent_incorrect_responses" in issues:
        triggers.append("repeated_incorrect_responses")
    if stats.get("performance_trend") == "declining":
        triggers.append("declining_recent_performance")
    if not triggers:
        return _decision("CONTINUE_PRIMARY", "no_diversion_rule_triggered", None, concept_evidence_ids,
                         "Available evidence does not meet a diversion rule; continue the current trajectory.",
                         source_reference, behavioral_reference, plan_reference)
    if not concept_evidence_ids:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "untraceable_support", None, [],
                         "A behavioral pattern is present but there are no concept-linked Phase 10 evidence references to support a diversion.",
                         source_reference, behavioral_reference, plan_reference)

    registry = dependency_registry or ConceptDependencyRegistry()
    dependencies = registry.supporting_concepts(
        trajectory["current_concept_id"], allow_synthetic=allow_synthetic_dependencies
    )
    if not dependencies:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "no_prerequisite_relationship", None,
                         concept_evidence_ids,
                         "Current performance may warrant investigation, but no sourced prerequisite/supporting relationship is configured. Do not invent a dependency.",
                         source_reference, behavioral_reference, plan_reference)
    dependency = dependencies[0]
    for candidate in dependencies:
        supporting_state = None
        supporting_estimate = None
        if behavioral_state is not None:
            supporting_state = next((item for item in behavioral_state["concept_states"]
                                     if item["concept_id"] == candidate["source_concept_id"]), None)
        if cognitive_state is not None:
            supporting_estimate = next((item for item in cognitive_state["concept_estimates"]
                                        if item["concept_id"] == candidate["source_concept_id"]), None)
        supporting = supporting_state or (supporting_estimate["observed_performance"] if supporting_estimate else None)
        supporting_sufficiency = (supporting_estimate["evidence_sufficiency"] if supporting_estimate
                                  else supporting.get("evidence_sufficiency", "none") if supporting else "none")
        interval = supporting.get("uncertainty_interval_95") if supporting else None
        interval_width = interval[1] - interval[0] if interval else None
        if (supporting is not None and int(supporting.get("attempts", 0)) >= 10
                and supporting_sufficiency in {"moderate", "high"}
                and supporting.get("recent_accuracy") is not None
                and supporting["recent_accuracy"] >= 0.80
                and supporting.get("performance_trend") in {"stable", "improving"}
                and interval_width is not None and interval_width <= 0.45):
            continue
        dependency = candidate
        break
    else:
        return _decision("REQUEST_ADDITIONAL_EVIDENCE", "supporting_concept_evidence_not_indicative_of_gap", None,
                         concept_evidence_ids,
                         "Available supporting-concept evidence does not indicate a reason to divert. Continue the primary path or collect a targeted diagnostic response; high observed performance is not treated as mastery.",
                         source_reference, behavioral_reference, plan_reference)
    return _decision("CREATE_DIVERSION", "+".join(triggers), dependency, concept_evidence_ids,
                     "Current response evidence and an explicitly configured supporting relationship justify a bounded diagnostic review. This does not establish a prerequisite deficit.",
                     source_reference, behavioral_reference, plan_reference,
                     dependency_status=dependency["verification_status"])


def _decision(action: str, rule_id: str, dependency: Mapping[str, Any] | None,
              evidence_ids: Sequence[str], explanation: str,
              cognitive_state_reference: Mapping[str, Any] | None = None,
              behavioral_state_reference: Mapping[str, Any] | None = None,
              representation_plan_reference: Mapping[str, Any] | None = None,
              dependency_status: str | None = None) -> dict[str, Any]:
    return {
        "action": action,
        "rule_id": rule_id,
        "target_concept_id": None if dependency is None else dependency["source_concept_id"],
        "dependency": None if dependency is None else dict(dependency),
        "dependency_verification_status": dependency_status,
        "supporting_evidence_ids": sorted(set(evidence_ids)),
        "cognitive_state_reference": None if cognitive_state_reference is None else dict(cognitive_state_reference),
        "behavioral_state_reference": None if behavioral_state_reference is None else dict(behavioral_state_reference),
        "representation_plan_reference": None if representation_plan_reference is None else dict(representation_plan_reference),
        "explanation": explanation,
    }
