"""Build evidence-linked, recommendation-only RepresentationPlan records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from ..cognitive_state.state_schema import validate_cognitive_state
from ..evidence.evidence_schema import validate_evidence
from ..learner_state.state_schema import validate_state as validate_behavioral_state
from .availability_registry import RepresentationAvailabilityRegistry
from .content_grounding import ConceptGrounding
from .decision_rules import evaluate_decision_rules
from .representation_schema import validate_representation_plan


def _stable_id(prefix: str, value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return prefix + hashlib.sha256(payload).hexdigest()[:32]


def _grounding_dict(value: ConceptGrounding | Mapping[str, Any] | None, concept_id: str) -> dict[str, Any]:
    if value is None:
        return {
            "concept_name": None,
            "name_status": "unavailable",
            "source_dataset": None,
            "related_skill_ids": [],
            "related_question_ids": [],
            "related_question_id_count": 0,
            "related_question_ids_truncated": False,
            "related_lecture_ids": [],
            "related_lecture_id_count": 0,
            "related_lecture_ids_truncated": False,
            "lecture_parts": [],
            "lecture_part_count": 0,
            "lecture_parts_truncated": False,
            "lecture_video_length_values": [],
            "lecture_video_length_count": 0,
            "lecture_video_lengths_truncated": False,
            "parts": [],
            "part_count": 0,
            "parts_truncated": False,
            "bundle_ids": [],
            "bundle_id_count": 0,
            "bundle_ids_truncated": False,
            "explanation_reference_ids": [],
            "explanation_reference_id_count": 0,
            "explanation_reference_ids_truncated": False,
            "learning_objective": None,
            "prerequisites": [],
            "example_ids": [],
            "representation_content_ids": [],
            "content_status": "unavailable",
            "limitations": ["No local concept or representation-content metadata was supplied."],
        }
    result = value.as_dict() if isinstance(value, ConceptGrounding) else dict(value)
    if result.get("concept_id") != concept_id:
        raise ValueError("concept grounding must match the requested concept_id")
    result.pop("concept_id", None)
    return result


def _evaluation_strategy(policy: Mapping[str, Any], selected_representation: str | None) -> list[dict[str, str]]:
    action = policy["selected_action"]
    if action in {"request_diagnostic_evidence", "request_additional_evidence"} or selected_representation == "diagnostic":
        method = "learner_explanation" if policy["conditions"]["inconsistent_responses"] else "follow_up_question"
        strategies = [{
            "method": method,
            "purpose": "Collect an additional observation relevant to the current concept and inspect the learner's response or reasoning.",
            "success_measure": "Record whether the requested response and reasoning were obtained; this measures evidence collection, not learning effectiveness.",
            "status": "recommended_only" if policy["conditions"]["inconsistent_responses"] else "requires_content_source",
        }]
    elif selected_representation == "worked_example":
        strategies = [{
            "method": "related_practice_question",
            "purpose": "After an available worked example is presented by a downstream component, observe a related response.",
            "success_measure": "Record correctness and the concept-linked evidence ID on the related response; a single result does not establish learning gain.",
            "status": "recommended_only",
        }]
    elif selected_representation in {"visual", "interactive", "simulation"}:
        method = "learner_explanation" if selected_representation == "visual" else "follow_up_question"
        strategies = [{
            "method": method,
            "purpose": "Collect a concept-aligned response after the registered representation is actually shown or used.",
            "success_measure": "Record the follow-up evidence and exposure status; do not treat it as a causal benefit estimate.",
            "status": "recommended_only",
        }]
    else:
        strategies = [{
            "method": "follow_up_question",
            "purpose": "Observe a related response after any downstream component supplies the planned content.",
            "success_measure": "Record response correctness and provenance; it is an observed outcome, not proof of understanding.",
            "status": "recommended_only",
        }]
    if policy["conditions"]["declining_recent_performance"]:
        strategies.append({
            "method": "prerequisite_check",
            "purpose": "Check concept prerequisites before attributing the observed decline to the selected representation.",
            "success_measure": "Record whether relevant prerequisite evidence is available; EdNet metadata does not define a prerequisite map.",
            "status": "requires_content_source",
        })
    return strategies


def _configuration(policy: Mapping[str, Any], registry: RepresentationAvailabilityRegistry) -> dict[str, Any]:
    representation_id = policy["selected_representation"]
    if representation_id is None:
        return {}
    capability = registry.get(representation_id)
    content = list(capability["content_ids"])
    config: dict[str, Any] = {}
    if representation_id in {"textual", "alternative_explanation", "symbolic"}:
        config["explanation_complexity"] = "simplified" if (
            policy["conditions"]["repeated_incorrect_responses"]
            or policy["conditions"]["declining_recent_performance"]
        ) else "standard"
    if representation_id == "worked_example":
        config.update({"example_count": 1, "difficulty_level": "similar_to_observed_items"})
    if representation_id == "visual":
        config["visual_detail_level"] = "moderate"
    if representation_id in {"interactive", "simulation"}:
        config["interaction_type"] = "content_provider_defined"
    if representation_id == "diagnostic":
        config["difficulty_level"] = "similar_to_observed_items"
    if content:
        config["required_content"] = content
    return config


def build_representation_plan(
    cognitive_state: Mapping[str, Any],
    concept_id: str,
    *,
    behavioral_state: Mapping[str, Any] | None = None,
    evidence_records: Sequence[Mapping[str, Any]] = (),
    registry: RepresentationAvailabilityRegistry | None = None,
    grounding: ConceptGrounding | Mapping[str, Any] | None = None,
    teaching_context: Mapping[str, Any] | None = None,
    prior_plan: Mapping[str, Any] | None = None,
    created_at: str | None = None,
    _state_prevalidated: bool = False,
) -> dict[str, Any]:
    """Build a rule-based plan without implying execution or learning benefit.

    Phase 11 embeds the relevant Phase 9 behavioral statistics in each concept
    estimate. A direct Phase 9 snapshot may also be passed; when supplied it is
    cross-checked against the Phase 11 projection before any rule runs.
    """
    if not _state_prevalidated:
        validate_cognitive_state(cognitive_state)
    learner_id = cognitive_state["learner_id"]
    if not concept_id:
        raise ValueError("concept_id is required")
    if prior_plan is not None:
        validate_representation_plan(prior_plan)
        if prior_plan["learner_id"] != learner_id or prior_plan["concept_id"] != concept_id:
            raise ValueError("prior plan must match the learner and concept")

    reference_ids = {item["evidence_id"] for item in cognitive_state["evidence_references"]}
    evidence_by_id: dict[str, Mapping[str, Any]] = {}
    for record in evidence_records:
        validate_evidence(record)
        if record["learner_id"] != learner_id:
            raise ValueError("evidence metadata must belong to the cognitive-state learner")
        if record["evidence_id"] not in reference_ids:
            raise ValueError("evidence metadata must be referenced by the supplied cognitive state")
        evidence_by_id[record["evidence_id"]] = record

    estimates = {item["concept_id"]: item for item in cognitive_state["concept_estimates"]}
    estimate = estimates.get(concept_id)
    if behavioral_state is not None:
        validate_behavioral_state(behavioral_state)
        if behavioral_state["learner_id"] != learner_id:
            raise ValueError("behavioral state must belong to the cognitive-state learner")
        reference = cognitive_state["observed_evidence_summary"]["phase9_state_reference"]
        if behavioral_state["state_timestamp"] != reference["state_timestamp"]:
            raise ValueError("behavioral state timestamp does not match the Phase 11 source reference")
        if estimate is not None:
            phase9_concept = next((item for item in behavioral_state["concept_states"] if item["concept_id"] == concept_id), None)
            if phase9_concept is None:
                raise ValueError("behavioral state lacks the concept included in the cognitive state")
            observed = estimate["observed_performance"]
            if any(phase9_concept[key] != observed[phase9_key] for key, phase9_key in (
                ("attempts", "attempts"), ("correct", "correct"), ("incorrect", "incorrect"),
                ("historical_accuracy", "historical_accuracy"), ("recent_accuracy", "recent_accuracy"),
                ("performance_trend", "performance_trend"),
            )):
                raise ValueError("Phase 9 concept statistics do not match the supplied Phase 11 estimate")

    registry = registry or RepresentationAvailabilityRegistry()
    grounding_doc = _grounding_dict(grounding, concept_id)
    prior_context = dict(prior_plan["teaching_context"]) if prior_plan is not None else {}
    supplied_context = dict(teaching_context or {})
    objective_default = {
        "objective_id": None,
        "description": grounding_doc.get("learning_objective"),
        "availability": "available" if grounding_doc.get("learning_objective") else "unavailable",
    }
    current_objective = supplied_context.get(
        "current_learning_objective", prior_context.get("current_learning_objective", objective_default)
    )
    if prior_plan is not None and current_objective != prior_context["current_learning_objective"]:
        raise ValueError("revised plans must preserve the prior learning objective in this phase")
    previous_plan_id = prior_plan["plan_id"] if prior_plan is not None else None
    context = {
        "current_concept_id": concept_id,
        "current_learning_objective": current_objective,
        "current_representation": supplied_context.get("current_representation", prior_context.get("current_representation")),
        "trajectory_id": supplied_context.get("trajectory_id", prior_context.get("trajectory_id")),
        "previous_plan_id": previous_plan_id,
        "branch_return_pointer": supplied_context.get("branch_return_pointer", prior_context.get("branch_return_pointer")),
        "prior_diagnostic_recommendation_ids": sorted(set(
            prior_context.get("prior_diagnostic_recommendation_ids", [])
            + (prior_plan["input_references"]["diagnostic_recommendation_ids"] if prior_plan else [])
        )),
        "evidence_history_ids": sorted(set(
            prior_context.get("evidence_history_ids", [])
            + (estimate["supporting_evidence_ids"] + estimate["contradictory_evidence_ids"] if estimate else [])
        )),
    }
    for key in ("trajectory_id", "branch_return_pointer", "current_representation"):
        if key in supplied_context:
            context[key] = supplied_context[key]
    if prior_plan is not None:
        for key in ("current_concept_id", "current_learning_objective", "current_representation", "trajectory_id", "branch_return_pointer"):
            if context[key] != prior_context[key]:
                raise ValueError(f"revised plans must preserve teaching-context field {key}")

    policy = evaluate_decision_rules(
        cognitive_state,
        concept_id,
        registry,
        evidence_records=list(evidence_by_id.values()),
        current_representation=context["current_representation"],
    )
    state_refs = cognitive_state["evidence_references"]
    reference_by_id = {item["evidence_id"]: item for item in state_refs}
    behavior_reference = behavioral_state and {
        "schema_version": behavioral_state["schema_version"],
        "state_timestamp": behavioral_state["state_timestamp"],
    }
    if behavior_reference is None:
        behavior_reference = dict(cognitive_state["observed_evidence_summary"]["phase9_state_reference"])

    input_references = {
        "cognitive_state_id": cognitive_state["cognitive_state_id"],
        "cognitive_state_version": cognitive_state["state_version"],
        "behavioral_state_reference": behavior_reference,
        "supporting_evidence_ids": sorted(set(policy["supporting_evidence_ids"])),
        "contradictory_evidence_ids": sorted(set(policy["contradictory_evidence_ids"])),
        "diagnostic_recommendation_ids": sorted({item["recommendation_id"] for item in policy["diagnostic_recommendations"]}),
    }
    evidence_history = sorted(set(context["evidence_history_ids"] + input_references["supporting_evidence_ids"] + input_references["contradictory_evidence_ids"]))
    context["evidence_history_ids"] = evidence_history
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    version = (prior_plan["plan_version"] + 1) if prior_plan is not None else 1
    plan_id = _stable_id("rp_", [learner_id, concept_id, cognitive_state["cognitive_state_id"], previous_plan_id, context, policy["selected_representation"], policy["selected_action"]])

    if grounding_doc["concept_name"]:
        target_concept = grounding_doc["concept_name"]
    else:
        target_concept = concept_id
    objective_text = grounding_doc.get("learning_objective")
    if policy["selected_action"] in {"request_diagnostic_evidence", "request_additional_evidence"}:
        intended_outcome = "Collect an additional concept-linked observation and reassess the provisional rule; no learning gain is assumed."
    elif policy["selected_representation"] is not None:
        intended_outcome = "Observe a concept-linked response after downstream delivery; correctness is an outcome, not proof of understanding or representation benefit."
    else:
        intended_outcome = "Retain context and wait for an available content capability or more concept-linked evidence."
    objective_status = "available" if objective_text else "unavailable"

    uncertainty = cognitive_state["uncertainty"]
    uncertainty_reasons = [
        f"{name}={uncertainty[name]}" for name in (
            "evidence_uncertainty", "temporal_uncertainty", "modality_uncertainty",
            "inference_uncertainty", "overall_uncertainty",
        )
    ]
    limitations = {
        "evidence": [
            "No concept estimate is present for the requested concept." if estimate is None else estimate["rationale"],
            "Available evidence is observational; no representation exposures or assigned actions are recorded.",
        ],
        "missing_modalities": list(cognitive_state["observed_evidence_summary"]["missing_modalities"]),
        "uncertainty": uncertainty_reasons + [
            reason for items in uncertainty["uncertainty_reasons"].values() for reason in items
        ],
        "unavailable_capabilities": [
            f"{item['representation_id']}: {item['reason']}"
            for item in registry.as_dict()["capabilities"] if item["status"] != "available"
        ],
        "claims_boundary": "This is a rule-based recommendation only. It does not infer learner modality preference, predict learning benefit, deliver content, or establish a cognitive state.",
    }
    plan = {
        "schema_version": "1.0",
        "taxonomy_version": registry.taxonomy_version,
        "plan_id": plan_id,
        "learner_id": learner_id,
        "concept_id": concept_id,
        "created_at": created_at,
        "plan_version": version,
        "previous_plan_id": previous_plan_id,
        "plan_kind": policy["plan_kind"] if prior_plan is None else ("revised" if policy["plan_kind"] != "continued" else "continued"),
        "input_references": input_references,
        "teaching_context": context,
        "concept_grounding": grounding_doc,
        "decision": {
            "selected_representation": policy["selected_representation"],
            "selected_action": policy["selected_action"],
            "delivery_status": policy["delivery_status"],
            "capability_reference": policy["capability_reference"],
            "decision_reason": policy["decision_reason"],
            "decision_method": "transparent_rules_v1",
            "decision_confidence": "low",
            "confidence_scope": "support_for_recommendation_not_learning_effect_or_modality_preference",
            "policy_trace": policy["policy_trace"],
            "alternative_representations": policy["alternative_representations"],
        },
        "learning_objective": {
            "target_concept": target_concept,
            "objective_text": objective_text,
            "objective_status": objective_status,
            "intended_learning_outcome": intended_outcome,
        },
        "representation_configuration": _configuration(policy, registry),
        "evaluation_strategy": _evaluation_strategy(policy, policy["selected_representation"]),
        "limitations": limitations,
    }
    validate_representation_plan(plan)
    return plan
