"""Schemas and validators for normalized evidence and evidence groups."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_SCHEMA_PATH = ROOT / "schemas" / "evidence_record_v1.schema.json"
GROUP_SCHEMA_PATH = ROOT / "schemas" / "evidence_group_v1.schema.json"
CONFLICT_SCHEMA_PATH = ROOT / "schemas" / "evidence_conflict_v1.schema.json"
ALIGNMENT_SCHEMA_PATH = ROOT / "schemas" / "evidence_alignment_v1.schema.json"
EVIDENCE_SCHEMA: dict[str, Any] = json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
GROUP_SCHEMA: dict[str, Any] = json.loads(GROUP_SCHEMA_PATH.read_text(encoding="utf-8"))
CONFLICT_SCHEMA: dict[str, Any] = json.loads(CONFLICT_SCHEMA_PATH.read_text(encoding="utf-8"))
ALIGNMENT_SCHEMA: dict[str, Any] = json.loads(ALIGNMENT_SCHEMA_PATH.read_text(encoding="utf-8"))
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None

_EVIDENCE_VALIDATOR = Draft202012Validator(EVIDENCE_SCHEMA, format_checker=FormatChecker()) if Draft202012Validator else None
_GROUP_VALIDATOR = Draft202012Validator(GROUP_SCHEMA, format_checker=FormatChecker()) if Draft202012Validator else None
_CONFLICT_VALIDATOR = Draft202012Validator(CONFLICT_SCHEMA, format_checker=FormatChecker()) if Draft202012Validator else None
_ALIGNMENT_VALIDATOR = Draft202012Validator(ALIGNMENT_SCHEMA, format_checker=FormatChecker()) if Draft202012Validator else None


def _validate(value: Mapping[str, Any], validator: Any, kind: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{kind} must be a JSON object")
    if validator is not None:
        errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise ValueError(f"{kind} fails schema at {location}: {first.message}")


def validate_evidence(record: Mapping[str, Any]) -> None:
    _validate(record, _EVIDENCE_VALIDATOR, "evidence record")
    if record.get("schema_version") != "1.0":
        raise ValueError("unsupported evidence schema version")
    if record.get("temporal", {}).get("sequence_number") is not None and record["temporal"]["sequence_number"] < 0:
        raise ValueError("sequence_number must be nonnegative")
    if not record.get("learner_id"):
        raise ValueError("learner_id is required")


def validate_group(group: Mapping[str, Any]) -> None:
    _validate(group, _GROUP_VALIDATOR, "evidence group")
    if group.get("schema_version") != "1.0":
        raise ValueError("unsupported evidence group schema version")
    if len(group.get("evidence_ids", [])) != len(set(group.get("evidence_ids", []))):
        raise ValueError("evidence group IDs must be unique")


def validate_conflict(conflict: Mapping[str, Any]) -> None:
    _validate(conflict, _CONFLICT_VALIDATOR, "evidence conflict")
    if conflict.get("schema_version") != "1.0":
        raise ValueError("unsupported evidence conflict schema version")
    if len(set(conflict.get("evidence_ids", []))) < 2:
        raise ValueError("a conflict requires at least two distinct evidence IDs")


def validate_alignment(alignment: Mapping[str, Any]) -> None:
    _validate(alignment, _ALIGNMENT_VALIDATOR, "evidence alignment")
    if alignment.get("schema_version") != "1.0":
        raise ValueError("unsupported evidence alignment schema version")
    if alignment.get("left_evidence_id") == alignment.get("right_evidence_id"):
        raise ValueError("alignment must refer to two distinct evidence IDs")
