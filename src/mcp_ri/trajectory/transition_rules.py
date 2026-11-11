"""Centralized, explicit trajectory state transitions."""

from __future__ import annotations

from typing import Any

ALLOWED_TRANSITIONS = {
    "CREATED": {"ACTIVE", "CANCELLED"},
    "ACTIVE": {"PAUSED", "DIVERTED", "COMPLETED", "REPLANNED", "CANCELLED"},
    "PAUSED": {"ACTIVE", "DIVERTED", "CANCELLED"},
    "DIVERTED": {"RESUMING", "PAUSED", "CANCELLED"},
    "RESUMING": {"ACTIVE", "DIVERTED", "REPLANNED", "COMPLETED", "CANCELLED"},
    "REPLANNED": {"ACTIVE", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def validate_transition(previous_state: str, new_state: str) -> None:
    if new_state not in ALLOWED_TRANSITIONS.get(previous_state, set()):
        raise ValueError(f"invalid trajectory transition: {previous_state} -> {new_state}")


def transition_record(trajectory: dict[str, Any], new_state: str) -> None:
    validate_transition(trajectory["current_status"], new_state)
    trajectory["current_status"] = new_state
