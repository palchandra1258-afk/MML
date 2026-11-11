"""Shared constants and deterministic IDs for trajectory records."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

SCHEMA_VERSION = "1.0"
TRAJECTORY_STATES = {
    "CREATED", "ACTIVE", "PAUSED", "DIVERTED", "RESUMING",
    "COMPLETED", "REPLANNED", "CANCELLED",
}
DIVERSION_STATES = {"ACTIVE", "RESOLVED", "CLOSED", "CANCELLED"}
RESUMPTION_OUTCOMES = {
    "RESUME_ORIGINAL_STEP", "RESUME_WITH_ALTERNATIVE_REPRESENTATION",
    "CONTINUE_DIVERSION", "REQUEST_ADDITIONAL_EVIDENCE",
    "REPLAN_PARENT_TRAJECTORY", "MARK_TRAJECTORY_COMPLETED",
}


def stable_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return prefix + hashlib.sha256(encoded).hexdigest()[:32]


def copy_record(value: Any) -> Any:
    return deepcopy(value)
