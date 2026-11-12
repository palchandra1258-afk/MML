"""Versioned taxonomy for representation recommendations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


TAXONOMY_VERSION = "1.0"

_TAXONOMY: tuple[dict[str, Any], ...] = (
    {
        "representation_id": "textual",
        "label": "Textual representation",
        "examples": ["simplified explanation", "concept definition", "alternative wording", "short summary"],
        "configuration_fields": ["explanation_complexity", "required_content"],
    },
    {
        "representation_id": "worked_example",
        "label": "Worked example",
        "examples": ["step-by-step solution", "solved problem", "worked example followed by similar practice"],
        "configuration_fields": ["example_count", "difficulty_level", "required_content"],
    },
    {
        "representation_id": "visual",
        "label": "Visual representation",
        "examples": ["concept diagram", "flow diagram", "graph", "annotated illustration", "visual comparison"],
        "configuration_fields": ["visual_detail_level", "required_content"],
    },
    {
        "representation_id": "symbolic",
        "label": "Symbolic representation",
        "examples": ["equation", "formula decomposition", "symbol manipulation", "algebraic transformations"],
        "configuration_fields": ["explanation_complexity", "required_content"],
    },
    {
        "representation_id": "interactive",
        "label": "Interactive representation",
        "examples": ["interactive graph", "parameter adjustment", "visual manipulation", "exploratory activity"],
        "configuration_fields": ["interaction_type", "difficulty_level", "required_content"],
    },
    {
        "representation_id": "simulation",
        "label": "Simulation",
        "examples": ["parameter-based simulation", "dynamic visualization", "what-if exploration"],
        "configuration_fields": ["interaction_type", "difficulty_level", "required_content"],
    },
    {
        "representation_id": "diagnostic",
        "label": "Diagnostic representation",
        "examples": ["diagnostic question", "conceptual assessment", "reasoning prompt", "intermediate-step request"],
        "configuration_fields": ["difficulty_level", "required_content"],
    },
    {
        "representation_id": "alternative_explanation",
        "label": "Alternative or continued explanation",
        "examples": ["continue current explanation", "simpler wording", "change explanation strategy", "different example"],
        "configuration_fields": ["explanation_complexity", "example_count", "required_content"],
    },
)

REPRESENTATION_IDS = tuple(item["representation_id"] for item in _TAXONOMY)
_BY_ID = {item["representation_id"]: item for item in _TAXONOMY}


def get_representation(representation_id: str) -> dict[str, Any]:
    try:
        return deepcopy(_BY_ID[representation_id])
    except KeyError as exc:
        raise ValueError(f"unknown representation category: {representation_id}") from exc


def taxonomy_document() -> dict[str, Any]:
    return {"taxonomy_version": TAXONOMY_VERSION, "representations": deepcopy(list(_TAXONOMY))}
