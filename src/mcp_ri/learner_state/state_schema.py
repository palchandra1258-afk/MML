"""Versioned learner-state JSON Schema and state-value validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "learner_state_v1.schema.json"
SCHEMA: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
try:
    from jsonschema import Draft202012Validator as _Draft202012Validator
except ImportError:
    _Draft202012Validator = None
_JSON_SCHEMA_VALIDATOR = _Draft202012Validator(SCHEMA) if _Draft202012Validator else None


def validate_state(state: Mapping[str, Any]) -> None:
    """Validate state structure and value invariants.

    The checked-in JSON Schema is the interchange contract. These checks cover
    its required structure plus the numeric invariants that JSON Schema cannot
    express conveniently for each state field.
    """
    if not isinstance(state, Mapping):
        raise ValueError("learner state must be a JSON object")
    required = set(SCHEMA["required"])
    missing = sorted(required - set(state))
    extra = sorted(set(state) - set(SCHEMA["properties"]))
    if missing or extra:
        raise ValueError(f"invalid learner state keys; missing={missing}, extra={extra}")
    if state["schema_version"] != "1.0":
        raise ValueError("unsupported learner-state schema_version")
    if not isinstance(state["learner_id"], str) or not state["learner_id"]:
        raise ValueError("learner_id must be a nonempty string")
    if state["state_timestamp"] is not None and not isinstance(state["state_timestamp"], str):
        raise ValueError("state_timestamp must be a string or null")
    if not isinstance(state["observation_window"], Mapping):
        raise ValueError("observation_window must be an object")
    if not isinstance(state["observation_summary"], Mapping):
        raise ValueError("observation_summary must be an object")
    if not isinstance(state["learning_performance"], Mapping):
        raise ValueError("learning_performance must be an object")
    if not isinstance(state["concept_states"], list):
        raise ValueError("concept_states must be an array")
    if not isinstance(state["model_predictions"], Mapping):
        raise ValueError("model_predictions must be an object")
    if not isinstance(state["limitations"], list) or not all(
        isinstance(item, str) for item in state["limitations"]
    ):
        raise ValueError("limitations must be an array of strings")

    # Validate against the complete checked-in JSON Schema when the optional
    # validator is installed. The checks below remain usable without it.
    if _JSON_SCHEMA_VALIDATOR is not None:
        errors = sorted(_JSON_SCHEMA_VALIDATOR.iter_errors(state), key=lambda e: list(e.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise ValueError(f"learner state fails JSON Schema at {location}: {first.message}")

    summary = state["observation_summary"]
    performance = state["learning_performance"]
    if summary["total_interactions"] != summary["labelled_responses"] + summary["unlabelled_interactions"]:
        raise ValueError("total_interactions must equal labelled plus unlabelled interactions")
    if performance["attempts"] != summary["labelled_responses"]:
        raise ValueError("learning_performance.attempts must match observation_summary.labelled_responses")
    if performance["correct"] + performance["incorrect"] != performance["attempts"]:
        raise ValueError("overall response counts do not sum to attempts")
    if summary["unique_concepts_observed"] != len(state["concept_states"]):
        raise ValueError("unique_concepts_observed must match concept_states length")
    concept_ids = [concept["concept_id"] for concept in state["concept_states"]]
    if len(concept_ids) != len(set(concept_ids)):
        raise ValueError("concept_states must contain unique concept IDs")
    for concept in state["concept_states"]:
        if concept["evidence_count"] != concept["attempts"]:
            raise ValueError(f"{concept['concept_id']} evidence_count must match attempts")

    for path, payload in (("learning_performance", state["learning_performance"]),):
        _validate_probabilities(payload, path)
    for index, concept in enumerate(state["concept_states"]):
        if not isinstance(concept, Mapping):
            raise ValueError(f"concept_states[{index}] must be an object")
        for key in ("concept_id", "performance_trend", "evidence_sufficiency",
                    "estimate_confidence", "uncertainty_level"):
            if key not in concept:
                raise ValueError(f"concept_states[{index}] missing {key}")
        if not isinstance(concept["concept_id"], str):
            raise ValueError(f"concept_states[{index}].concept_id must be a string")
        for key in ("attempts", "correct", "incorrect", "evidence_count"):
            if not isinstance(concept.get(key), int) or concept[key] < 0:
                raise ValueError(f"concept_states[{index}].{key} must be a nonnegative integer")
        if concept["correct"] + concept["incorrect"] != concept["attempts"]:
            raise ValueError(f"concept_states[{index}] response counts do not sum to attempts")
        _validate_probabilities(concept, f"concept_states[{index}]")
        if not isinstance(concept.get("potential_issues"), list) or not all(
            isinstance(item, str) for item in concept["potential_issues"]
        ):
            raise ValueError(f"concept_states[{index}].potential_issues must be strings")


def _validate_probabilities(payload: Mapping[str, Any], path: str) -> None:
    for key in ("historical_accuracy", "recent_accuracy", "smoothed_performance",
                "estimated_performance", "recent_performance", "historical_performance",
                "performance_change"):
        if key not in payload:
            continue
        value = payload[key]
        if value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{path}.{key} must be numeric or null")
        if key == "performance_change":
            if not -1.0 <= float(value) <= 1.0:
                raise ValueError(f"{path}.{key} must be in [-1, 1]")
        elif not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{path}.{key} must be in [0, 1]")
    interval = payload.get("uncertainty_interval_95")
    if interval is not None:
        if (not isinstance(interval, list) or len(interval) != 2
                or not all(isinstance(x, (int, float)) for x in interval)
                or not 0.0 <= interval[0] <= interval[1] <= 1.0):
            raise ValueError(f"{path}.uncertainty_interval_95 must be an ordered [0,1] pair")
