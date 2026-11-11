"""Versioned schema and semantic checks for provisional cognitive states."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "cognitive_state_v1.schema.json"
SCHEMA: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None
_VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker()) if Draft202012Validator else None


def validate_cognitive_state(state: Mapping[str, Any]) -> None:
    if not isinstance(state, Mapping):
        raise ValueError("cognitive state must be an object")
    if _VALIDATOR is not None:
        errors = sorted(_VALIDATOR.iter_errors(state), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise ValueError(f"cognitive state fails schema at {location}: {first.message}")
    if state.get("schema_version") != "1.0":
        raise ValueError("unsupported cognitive-state schema version")
    if not state.get("learner_id"):
        raise ValueError("cognitive-state learner_id is required")
    if state["state_version"] == 1 and state["previous_state_id"] is not None:
        raise ValueError("initial cognitive state cannot have a previous_state_id")
    if state["state_version"] > 1 and state["previous_state_id"] is None:
        raise ValueError("updated cognitive state must link to its previous state")

    references = state["evidence_references"]
    evidence_ids = [item["evidence_id"] for item in references]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("evidence_references must have unique evidence IDs")
    evidence_id_set = set(evidence_ids)
    estimates = state["concept_estimates"]
    concept_ids = [item["concept_id"] for item in estimates]
    if len(concept_ids) != len(set(concept_ids)):
        raise ValueError("concept_estimates must have unique concept IDs")
    if set(concept_ids) != set(state["relevant_concept_ids"]):
        raise ValueError("relevant_concept_ids must match concept_estimates")
    for item in estimates:
        if not item["supporting_evidence_ids"]:
            raise ValueError(f"{item['concept_id']} estimate must cite supporting evidence")
        observed = item["observed_performance"]
        if observed["correct"] + observed["incorrect"] != observed["attempts"]:
            raise ValueError(f"{item['concept_id']} response counts do not sum to attempts")
        for relation in ("supporting_evidence_ids", "contradictory_evidence_ids"):
            unknown = set(item[relation]) - evidence_id_set
            if unknown:
                raise ValueError(f"{item['concept_id']} {relation} contain unknown evidence IDs")

    hypotheses = state["possible_difficulty_hypotheses"]
    hypothesis_ids = [item["hypothesis_id"] for item in hypotheses]
    if len(hypothesis_ids) != len(set(hypothesis_ids)):
        raise ValueError("possible_difficulty_hypotheses must have unique IDs")
    for item in hypotheses:
        if item["concept_id"] is not None and item["concept_id"] not in set(concept_ids):
            raise ValueError("hypothesis concept_id must refer to an estimated concept")
        if set(item["supporting_evidence_ids"]) - evidence_id_set:
            raise ValueError("hypothesis contains an unknown supporting evidence ID")
        if set(item["contradictory_evidence_ids"]) - evidence_id_set:
            raise ValueError("hypothesis contains an unknown contradictory evidence ID")

    hypothesis_id_set = set(hypothesis_ids)
    for item in state["diagnostic_recommendations"]:
        if set(item["supporting_hypothesis_ids"]) - hypothesis_id_set:
            raise ValueError("diagnostic recommendation contains an unknown hypothesis ID")
        if set(item["supporting_evidence_ids"]) - evidence_id_set:
            raise ValueError("diagnostic recommendation contains an unknown evidence ID")

    summary = state["observed_evidence_summary"]
    if summary["contradictory_evidence_count"] != len(summary["contradictory_evidence_ids"]):
        raise ValueError("contradictory_evidence_count must match conflict records")
    if set(summary["available_modalities"]) & set(summary["missing_modalities"]):
        raise ValueError("a modality cannot be both available and missing")
