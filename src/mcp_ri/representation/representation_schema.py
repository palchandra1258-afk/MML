"""JSON Schema and cross-reference validation for RepresentationPlan v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .representation_taxonomy import REPRESENTATION_IDS


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "representation_plan_v1.schema.json"
SCHEMA: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None
_VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker()) if Draft202012Validator else None


def validate_representation_plan(plan: Mapping[str, Any]) -> None:
    if not isinstance(plan, Mapping):
        raise ValueError("representation plan must be an object")
    if _VALIDATOR is not None:
        errors = sorted(_VALIDATOR.iter_errors(plan), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise ValueError(f"representation plan fails schema at {location}: {first.message}")
    if plan.get("schema_version") != "1.0":
        raise ValueError("unsupported representation-plan schema version")
    if plan["concept_id"] != plan["teaching_context"]["current_concept_id"]:
        raise ValueError("plan concept_id must match the preserved current teaching concept")
    if plan["previous_plan_id"] != plan["teaching_context"]["previous_plan_id"]:
        raise ValueError("top-level and teaching-context previous_plan_id must match")
    if plan["plan_version"] == 1 and plan["previous_plan_id"] is not None:
        raise ValueError("initial plan cannot have previous_plan_id")
    if plan["plan_version"] > 1 and plan["previous_plan_id"] is None:
        raise ValueError("revised plan must reference its previous plan")

    decision = plan["decision"]
    selected = decision["selected_representation"]
    alternatives = decision["alternative_representations"]
    if selected is None:
        if decision["delivery_status"] != "not_selected" or decision["capability_reference"] is not None:
            raise ValueError("a plan without a selected representation cannot claim a delivery capability")
        if decision["selected_action"] not in {"request_diagnostic_evidence", "request_additional_evidence", "defer_until_capability_available"}:
            raise ValueError("a plan without a representation must request evidence or defer")
    else:
        if selected not in REPRESENTATION_IDS:
            raise ValueError("selected representation is outside the versioned taxonomy")
        capability = decision["capability_reference"]
        if decision["delivery_status"] != "available" or not isinstance(capability, Mapping):
            raise ValueError("an unavailable representation cannot be selected as executable")
        if capability.get("representation_id") != selected or capability.get("status") != "available":
            raise ValueError("selected representation must match an available capability reference")
        if not (capability.get("provider_id") or capability.get("content_ids")):
            raise ValueError("selected capability requires a provider_id or concrete content_ids")
        if decision["selected_action"] not in {"recommend_representation", "continue_current_representation"}:
            raise ValueError("selected representation is inconsistent with selected_action")

    alternative_ids = [item["representation_id"] for item in alternatives]
    if len(alternative_ids) != len(set(alternative_ids)):
        raise ValueError("alternative representations must be unique")
    if selected in alternative_ids:
        raise ValueError("selected representation must not also be listed as an alternative")
    if selected is not None:
        marked_selected = [item for item in alternatives if item["selection_status"] == "selected"]
        if marked_selected:
            raise ValueError("alternative list cannot mark a category selected")

    grounding = plan["concept_grounding"]
    for values_key, count_key, truncated_key in (
        ("related_question_ids", "related_question_id_count", "related_question_ids_truncated"),
        ("related_lecture_ids", "related_lecture_id_count", "related_lecture_ids_truncated"),
        ("lecture_parts", "lecture_part_count", "lecture_parts_truncated"),
        ("lecture_video_length_values", "lecture_video_length_count", "lecture_video_lengths_truncated"),
        ("parts", "part_count", "parts_truncated"),
        ("bundle_ids", "bundle_id_count", "bundle_ids_truncated"),
        ("explanation_reference_ids", "explanation_reference_id_count", "explanation_reference_ids_truncated"),
    ):
        actual_count = len(grounding[values_key])
        declared_count = grounding[count_key]
        if declared_count < actual_count:
            raise ValueError(f"{count_key} cannot be smaller than the included {values_key}")
        if grounding[truncated_key] != (declared_count > actual_count):
            raise ValueError(f"{truncated_key} must report whether {values_key} was truncated")

    referenced_evidence = (
        set(plan["input_references"]["supporting_evidence_ids"])
        | set(plan["input_references"]["contradictory_evidence_ids"])
    )
    for rule in decision["policy_trace"]:
        if set(rule["evidence_ids"]) - referenced_evidence:
            raise ValueError("policy trace refers to evidence absent from input_references")
    for evidence_id in plan["teaching_context"]["evidence_history_ids"]:
        if not isinstance(evidence_id, str) or not evidence_id.startswith("ev_"):
            raise ValueError("evidence_history_ids must contain evidence IDs")
