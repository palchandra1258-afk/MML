"""Append-only event history with trajectory reconstruction and diversion lookup."""

from __future__ import annotations

from typing import Any, Mapping

from .models import copy_record, stable_id
from .schemas import HISTORY_EVENT_SCHEMA, validate_document
from .validator import validate_context_snapshot, validate_diversion, validate_trajectory


class TrajectoryHistory:
    """In-memory append-only store matching Phase 11/12 history conventions.

    Callers can serialize `events` and the referenced snapshots to JSONL or a
    database. This object intentionally does not claim durable persistence.
    """

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._versions: dict[str, dict[int, dict[str, Any]]] = {}
        self._diversions: dict[str, list[dict[str, Any]]] = {}
        self._contexts: dict[str, dict[str, Any]] = {}

    @property
    def events(self) -> list[dict[str, Any]]:
        return [copy_record(event) for trajectory_events in self._events.values() for event in trajectory_events]

    def append_context_snapshot(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        item = copy_record(snapshot)
        validate_context_snapshot(item)
        parent_versions = self._versions.get(item["parent_trajectory_id"], {})
        parent = parent_versions.get(item["parent_trajectory_version"])
        if parent is None:
            raise ValueError("context snapshot must reference an existing parent trajectory version")
        if (parent["learner_id"] != item["learner_id"]
                or parent["target_concept_id"] != item["original_target_concept_id"]
                or parent["primary_learning_goal"] != item["primary_learning_goal"]
                or parent["current_learning_step"] != item["current_learning_step"]
                or parent["completed_steps"] != item["completed_steps"]
                or parent["pending_steps"] != item["pending_steps"]
                or parent["context"]["previous_representation_plan_id"] != item["previous_representation_plan_id"]
                or parent["context"]["previous_cognitive_state_id"] != item["previous_cognitive_state_id"]
                or not set(parent["context"]["supporting_evidence_ids"]) <= set(item["supporting_evidence_ids"])
                or parent["orchestration"]["current_depth"] != item["original_current_depth"]
                or parent["current_status"] != item["original_trajectory_status"]):
            raise ValueError("context snapshot does not preserve the referenced parent trajectory version")
        key = item["context_snapshot_id"]
        if key in self._contexts and self._contexts[key] != item:
            raise ValueError("context snapshot ID collision")
        self._contexts.setdefault(key, item)
        return copy_record(self._contexts[key])

    def get_context_snapshot(self, context_snapshot_id: str) -> dict[str, Any]:
        if context_snapshot_id not in self._contexts:
            raise KeyError(context_snapshot_id)
        return copy_record(self._contexts[context_snapshot_id])

    def append_diversion(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        diversion = copy_record(candidate)
        validate_diversion(diversion)
        parent = self._versions.get(diversion["parent_trajectory_id"], {}).get(diversion["parent_trajectory_version"])
        context = self._contexts.get(diversion["context_snapshot_id"])
        if parent is None or context is None:
            raise ValueError("diversion must refer to an existing parent trajectory version and context snapshot")
        if (parent["learner_id"] != diversion["learner_id"]
                or context["parent_trajectory_id"] != diversion["parent_trajectory_id"]
                or context["parent_trajectory_version"] != diversion["parent_trajectory_version"]
                or parent["current_concept_id"] != diversion["parent_concept_id"]
                or parent["primary_learning_goal"] != diversion["parent_learning_objective"]
                or parent["current_learning_step"] != diversion["previous_learning_step"]
                or parent["current_status"] != diversion["original_trajectory_status"]
                or parent["context"]["previous_representation_plan_id"] != diversion["previous_representation_plan_id"]
                or context["context_snapshot_id"] != diversion["context_snapshot_id"]):
            raise ValueError("diversion parent/context links do not match the authoritative trajectory snapshot")
        history = self._diversions.setdefault(diversion["diversion_id"], [])
        if history:
            prior = history[-1]
            if diversion == prior:
                return copy_record(prior)
            if diversion["diversion_version"] != prior["diversion_version"] + 1:
                raise ValueError("diversion versions must be consecutive")
            if diversion["parent_trajectory_id"] != prior["parent_trajectory_id"]:
                raise ValueError("a diversion cannot change parent trajectory")
        elif diversion["diversion_version"] != 1:
            raise ValueError("initial diversion version must be 1")
        history.append(diversion)
        return copy_record(diversion)

    def latest_diversion(self, diversion_id: str) -> dict[str, Any]:
        if diversion_id not in self._diversions:
            raise KeyError(diversion_id)
        return copy_record(self._diversions[diversion_id][-1])

    def diversions_for_trajectory(self, trajectory_id: str) -> list[dict[str, Any]]:
        return [copy_record(versions[-1]) for versions in self._diversions.values()
                if versions[-1]["parent_trajectory_id"] == trajectory_id]

    def all_diversions(self) -> list[dict[str, Any]]:
        return [copy_record(versions[-1]) for versions in self._diversions.values()]

    @property
    def diversion_versions(self) -> list[dict[str, Any]]:
        return [copy_record(item) for versions in self._diversions.values() for item in versions]

    @property
    def context_snapshots(self) -> list[dict[str, Any]]:
        return copy_record(list(self._contexts.values()))

    def parent_trajectory_of_diversion(self, diversion_id: str) -> str:
        return self.latest_diversion(diversion_id)["parent_trajectory_id"]

    def append_event(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        event = copy_record(candidate)
        validate_document(event, HISTORY_EVENT_SCHEMA, "trajectory history event")
        trajectory = event["trajectory_snapshot"]
        validate_trajectory(trajectory)
        if trajectory["trajectory_id"] != event["trajectory_id"] or trajectory["learner_id"] != event["learner_id"]:
            raise ValueError("history event and trajectory snapshot identity mismatch")
        if trajectory["trajectory_version"] != event["trajectory_version"]:
            raise ValueError("history event version must match its trajectory snapshot")
        if trajectory["current_status"] != event["new_state"]:
            raise ValueError("history event new_state must match its trajectory snapshot")
        history = self._events.setdefault(event["trajectory_id"], [])
        if any(old["event_id"] == event["event_id"] for old in history):
            existing = next(old for old in history if old["event_id"] == event["event_id"])
            if existing == event:
                return copy_record(existing)
            raise ValueError("event ID reused with different contents")
        previous = history[-1] if history else None
        expected_previous = previous["event_id"] if previous else None
        if event["previous_event_id"] != expected_previous:
            raise ValueError("previous_event_id must link the append-only trajectory history")
        if previous is None:
            if event["trajectory_version"] != 1 or event["event_type"] != "TRAJECTORY_CREATED":
                raise ValueError("the first trajectory history event must create version 1")
        else:
            old_version = previous["trajectory_version"]
            new_version = event["trajectory_version"]
            if new_version not in {old_version, old_version + 1}:
                raise ValueError("trajectory history versions must stay current or increment by one")
            if new_version == old_version and trajectory != previous["trajectory_snapshot"]:
                raise ValueError("same-version history events cannot mutate the trajectory snapshot")
            if new_version == old_version + 1 and event["previous_state"] != previous["new_state"]:
                raise ValueError("new trajectory version must record the preceding state")
        versions = self._versions.setdefault(event["trajectory_id"], {})
        if event["trajectory_version"] in versions and versions[event["trajectory_version"]] != trajectory:
            raise ValueError("trajectory version is immutable")
        versions.setdefault(event["trajectory_version"], copy_record(trajectory))
        history.append(event)
        return copy_record(event)

    def history_for_trajectory(self, trajectory_id: str) -> list[dict[str, Any]]:
        return copy_record(self._events.get(trajectory_id, []))

    def reconstruct(self, trajectory_id: str, version: int | None = None) -> dict[str, Any]:
        versions = self._versions.get(trajectory_id, {})
        if not versions:
            raise KeyError(trajectory_id)
        selected = max(versions) if version is None else int(version)
        if selected not in versions:
            raise KeyError(f"trajectory {trajectory_id} has no version {selected}")
        return copy_record(versions[selected])

    def inspect_transition(self, event_id: str) -> dict[str, Any]:
        for event in self.events:
            if event["event_id"] == event_id:
                return copy_record(event)
        raise KeyError(event_id)

    def build_event(self, *, trajectory: Mapping[str, Any], event_type: str, occurred_at: str,
                    previous_state: str | None, trigger: str, supporting_evidence_ids: list[str],
                    cognitive_state_reference: Mapping[str, Any] | None,
                    representation_plan_reference: Mapping[str, Any] | None,
                    related_diversion_id: str | None, decision_explanation: str) -> dict[str, Any]:
        events = self._events.get(trajectory["trajectory_id"], [])
        previous_id = events[-1]["event_id"] if events else None
        next_event_id = stable_id("tevt_", [trajectory["trajectory_id"], trajectory["trajectory_version"],
                                             len(events) + 1, event_type, trigger, related_diversion_id])
        return {
            "schema_version": "1.0", "event_id": next_event_id,
            "learner_id": trajectory["learner_id"], "trajectory_id": trajectory["trajectory_id"],
            "trajectory_version": trajectory["trajectory_version"], "previous_event_id": previous_id,
            "event_type": event_type, "occurred_at": occurred_at,
            "previous_state": previous_state, "new_state": trajectory["current_status"],
            "trigger": trigger, "supporting_evidence_ids": sorted(set(supporting_evidence_ids)),
            "cognitive_state_reference": copy_record(cognitive_state_reference),
            "representation_plan_reference": copy_record(representation_plan_reference),
            "related_diversion_id": related_diversion_id,
            "decision_explanation": decision_explanation,
            "trajectory_snapshot": copy_record(trajectory),
        }
