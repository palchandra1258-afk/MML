"""JSON Schema loading for the independent Phase 13 records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"


def load_schema(filename: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))


TRAJECTORY_SCHEMA = load_schema("learning_trajectory_v1.schema.json")
DIVERSION_SCHEMA = load_schema("learning_diversion_v1.schema.json")
CONTEXT_SCHEMA = load_schema("trajectory_context_snapshot_v1.schema.json")
DEPENDENCY_SCHEMA = load_schema("concept_dependency_registry_v1.schema.json")
HISTORY_EVENT_SCHEMA = load_schema("trajectory_history_event_v1.schema.json")

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - project requirements install jsonschema
    Draft202012Validator = None


def validate_document(document: Mapping[str, Any], schema: Mapping[str, Any], label: str) -> None:
    if not isinstance(document, Mapping):
        raise ValueError(f"{label} must be an object")
    if Draft202012Validator is None:
        return
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = ".".join(map(str, first.path)) or "<root>"
        raise ValueError(f"{label} fails schema at {location}: {first.message}")
