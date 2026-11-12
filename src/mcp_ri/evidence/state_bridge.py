"""Explicit bridge from normalized interaction evidence to Phase 9 updates."""

from __future__ import annotations

from typing import Any, Mapping

from ..learner_state.state_builder import LearnerStateAccumulator


def phase9_row_from_interaction(record: Mapping[str, Any]) -> dict[str, Any]:
    if record.get("evidence_type") != "interaction":
        raise ValueError("only interaction evidence can update the Phase 9 behavioral state")
    content = record["content"]
    temporal = record["temporal"]
    sequence = temporal.get("sequence_number")
    return {
        "learner_id": record["learner_id"],
        "source_row_order": sequence,
        "timestamp": temporal.get("event_timestamp"),
        "question_id": content.get("question_id"),
        "correctness": content.get("correctness"),
        "skill_tags": ";".join(content.get("skill_ids", [])),
        "is_exact_duplicate": "1" if content.get("is_exact_duplicate") else "0",
    }


def apply_interaction_evidence(accumulator: LearnerStateAccumulator, record: Mapping[str, Any]) -> dict[str, Any]:
    if accumulator.learner_id != record.get("learner_id"):
        raise ValueError("interaction learner_id does not match Phase 9 state")
    accumulator.update(phase9_row_from_interaction(record))
    return accumulator.snapshot()
