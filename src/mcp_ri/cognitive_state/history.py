"""Append-only in-memory history of successive cognitive-state estimates."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .state_schema import validate_cognitive_state


def _copy_state(state: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(state), ensure_ascii=False))


class CognitiveStateHistory:
    """Keep immutable snapshots and explicit links between successive versions."""

    def __init__(self, learner_id: str) -> None:
        if not learner_id:
            raise ValueError("learner_id is required")
        self.learner_id = str(learner_id)
        self._states: list[dict[str, Any]] = []

    @property
    def states(self) -> list[dict[str, Any]]:
        return [_copy_state(state) for state in self._states]

    @property
    def latest(self) -> dict[str, Any] | None:
        return _copy_state(self._states[-1]) if self._states else None

    def append(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        state = _copy_state(candidate)
        validate_cognitive_state(state)
        if state["learner_id"] != self.learner_id:
            raise ValueError("cognitive state learner_id does not match this history")
        if any(existing["cognitive_state_id"] == state["cognitive_state_id"] for existing in self._states):
            raise ValueError("this cognitive-state snapshot is already present")

        prior = self._states[-1] if self._states else None
        if prior is not None:
            old_end = prior["observation_window"]["sequence_end"]
            new_end = state["observation_window"]["sequence_end"]
            if old_end is not None and new_end is not None and new_end < old_end:
                raise ValueError("cognitive-state sequence_end must be nondecreasing")
            old_status = {item["concept_id"]: item["estimated_learning_status"] for item in prior["concept_estimates"]}
            new_status = {item["concept_id"]: item["estimated_learning_status"] for item in state["concept_estimates"]}
            concept_changes = [
                {"concept_id": concept_id, "from_status": old_status.get(concept_id), "to_status": new_status.get(concept_id)}
                for concept_id in sorted(set(old_status) | set(new_status))
                if old_status.get(concept_id) != new_status.get(concept_id)
            ]
            old_hypotheses = {item["hypothesis_id"] for item in prior["possible_difficulty_hypotheses"]}
            new_hypotheses = {item["hypothesis_id"] for item in state["possible_difficulty_hypotheses"]}
            old_evidence = {item["evidence_id"] for item in prior["evidence_references"]}
            new_evidence = {item["evidence_id"] for item in state["evidence_references"]}
            notes = ["A new immutable estimate was appended; the previous cognitive-state record remains unchanged."]
            if concept_changes:
                notes.append("One or more provisional concept categories changed.")
            state["state_version"] = prior["state_version"] + 1
            state["previous_state_id"] = prior["cognitive_state_id"]
            state["state_change_summary"] = {
                "concept_status_changes": concept_changes,
                "hypothesis_ids_added": sorted(new_hypotheses - old_hypotheses),
                "hypothesis_ids_no_longer_emitted": sorted(old_hypotheses - new_hypotheses),
                "evidence_ids_added": sorted(new_evidence - old_evidence),
                "change_notes": notes,
            }
        validate_cognitive_state(state)
        self._states.append(state)
        return _copy_state(state)
