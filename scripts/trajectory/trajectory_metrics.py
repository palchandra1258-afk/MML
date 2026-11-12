"""Shared validation and metrics for exported trajectory histories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_ri.trajectory.history import TrajectoryHistory
from mcp_ri.trajectory.schemas import DEPENDENCY_SCHEMA, validate_document
from mcp_ri.trajectory.transition_rules import ALLOWED_TRANSITIONS, validate_transition
from mcp_ri.trajectory.validator import validate_trajectory


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSONL: {exc}") from exc
    return records


def pct(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else round(100.0 * numerator / denominator, 4)


def validate_artifacts(run_dir: Path) -> tuple[TrajectoryHistory, dict[str, list[dict[str, Any]]]]:
    required = {
        "trajectories": run_dir / "trajectories.jsonl",
        "diversions": run_dir / "diversions.jsonl",
        "contexts": run_dir / "context_snapshots.jsonl",
        "events": run_dir / "history_events.jsonl",
        "decisions": run_dir / "decisions.jsonl",
    }
    for name, path in required.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing {name} artifact: {path}")
    records = {name: read_jsonl(path) for name, path in required.items()}
    history = TrajectoryHistory()
    for event in records["events"]:
        history.append_event(event)
    for snapshot in records["contexts"]:
        history.append_context_snapshot(snapshot)
    for diversion in sorted(records["diversions"], key=lambda item: (item["diversion_id"], item["diversion_version"])):
        history.append_diversion(diversion)
    for trajectory in records["trajectories"]:
        validate_trajectory(trajectory)
        reconstructed = history.reconstruct(trajectory["trajectory_id"])
        if trajectory != reconstructed:
            raise ValueError(f"latest exported trajectory differs from history reconstruction: {trajectory['trajectory_id']}")
    dependency_path = run_dir / "dependency_registry.json"
    dependency_doc = json.loads(dependency_path.read_text(encoding="utf-8"))
    validate_document(dependency_doc, DEPENDENCY_SCHEMA, "dependency registry")
    return history, records


def evaluate_records(history: TrajectoryHistory, records: dict[str, list[dict[str, Any]]],
                     cognitive_states: dict[str, dict[str, Any]] | None = None,
                     max_diversion_depth: int = 1) -> dict[str, Any]:
    events = records["events"]
    trajectories = records["trajectories"]
    diversions = records["diversions"]
    contexts = {item["context_snapshot_id"]: item for item in records["contexts"]}
    trajectory_by_id = {item["trajectory_id"]: item for item in trajectories}
    created_diversions = {item["diversion_id"]: item for item in diversions if item["diversion_version"] == 1}

    transition_events = [event for event in events
                         if event["previous_state"] is not None and event["new_state"] != event["previous_state"]]
    valid_transition_count = 0
    for event in transition_events:
        try:
            validate_transition(event["previous_state"], event["new_state"])
            valid_transition_count += 1
        except ValueError:
            pass
    states = sorted(ALLOWED_TRANSITIONS)
    invalid_edges = [(old, new) for old in states for new in states
                     if new not in ALLOWED_TRANSITIONS[old]]
    rejected_invalid_edges = 0
    for old, new in invalid_edges:
        try:
            validate_transition(old, new)
        except ValueError:
            rejected_invalid_edges += 1

    context_valid = 0
    parent_valid = 0
    depth_valid = 0
    event_diversion_ids = {event["related_diversion_id"] for event in events
                           if event["related_diversion_id"]}
    creation_events = [event for event in events if event["event_type"] == "DIVERSION_CREATED"]
    for diversion_id, diversion in created_diversions.items():
        snapshot = contexts.get(diversion["context_snapshot_id"])
        event = next((item for item in creation_events if item["related_diversion_id"] == diversion_id), None)
        parent_id = diversion["parent_trajectory_id"]
        parent_exists = parent_id in trajectory_by_id
        if (parent_exists and snapshot is not None
                and snapshot["parent_trajectory_id"] == parent_id
                and snapshot["context_snapshot_id"] == diversion["context_snapshot_id"]
                and snapshot["parent_trajectory_version"] == diversion["parent_trajectory_version"]):
            parent_valid += 1
            original = history.reconstruct(parent_id, diversion["parent_trajectory_version"])
            if (snapshot["current_learning_step"] == original["current_learning_step"]
                    and snapshot["completed_steps"] == original["completed_steps"]
                    and snapshot["pending_steps"] == original["pending_steps"]
                    and snapshot["original_target_concept_id"] == original["target_concept_id"]
                    and snapshot["previous_representation_plan_id"] == original["context"]["previous_representation_plan_id"]
                    and snapshot["previous_cognitive_state_id"] == original["context"]["previous_cognitive_state_id"]):
                context_valid += 1
        if (event is not None and event["trajectory_snapshot"]["orchestration"]["current_depth"] <= max_diversion_depth
                and event["trajectory_snapshot"]["orchestration"]["active_diversion_id"] == diversion_id):
            depth_valid += 1

    latest_diversions: dict[str, dict[str, Any]] = {}
    for item in diversions:
        prior = latest_diversions.get(item["diversion_id"])
        if prior is None or item["diversion_version"] > prior["diversion_version"]:
            latest_diversions[item["diversion_id"]] = item
    active = [item for item in latest_diversions.values() if item["diversion_status"] == "ACTIVE"]
    active_duplicate_pairs = 0
    for index, left in enumerate(active):
        for right in active[index + 1:]:
            if (left["learner_id"] == right["learner_id"]
                    or (left["parent_trajectory_id"] == right["parent_trajectory_id"]
                        and left["diversion_concept_id"] == right["diversion_concept_id"])):
                active_duplicate_pairs += 1

    reconstructed_events = sum(
        history.reconstruct(event["trajectory_id"], event["trajectory_version"]) == event["trajectory_snapshot"]
        for event in events
    )
    evidence_checks = []
    if cognitive_states is not None:
        for row in records["decisions"]:
            state = cognitive_states.get(row["cognitive_state_id"])
            if state is not None:
                references = {item["evidence_id"] for item in state["evidence_references"]}
                evidence_checks.append(set(row["decision"]["supporting_evidence_ids"]) <= references)
            else:
                evidence_checks.append(False)
    resumption_events = [event for event in events if event["event_type"] == "RESUMPTION_DECIDED"]
    resumption_traceable = [bool(event["trigger"] and event["decision_explanation"]
                                 and event["related_diversion_id"] in created_diversions
                                 and (not event["supporting_evidence_ids"] or event["cognitive_state_reference"] is not None))
                           for event in resumption_events]
    deterministic = [row["deterministic_replay_match"] for row in records["decisions"]]
    return {
        "status": "complete",
        "trajectory_count": len(trajectories),
        "diversion_count": len(created_diversions),
        "transition_count": len(transition_events),
        "valid_transition_count": valid_transition_count,
        "valid_transition_rate_percent": pct(valid_transition_count, len(transition_events)),
        "illegal_transition_edges_tested": len(invalid_edges),
        "invalid_transition_rejection_count": rejected_invalid_edges,
        "invalid_transition_rejection_rate_percent": pct(rejected_invalid_edges, len(invalid_edges)),
        "context_snapshots_preserved": context_valid,
        "context_preservation_rate_percent": pct(context_valid, len(created_diversions)),
        "parent_child_relationships_valid": parent_valid,
        "parent_child_relationship_validity_percent": pct(parent_valid, len(created_diversions)),
        "diversion_creation_events": len(creation_events),
        "diversion_creation_consistency_percent": pct(
            sum(item["related_diversion_id"] in created_diversions for item in creation_events), len(creation_events)),
        "active_duplicate_pairs": active_duplicate_pairs,
        "duplicate_active_diversion_rate_percent": pct(active_duplicate_pairs, len(active)),
        "history_event_reconstruction_matches": reconstructed_events,
        "history_event_count": len(events),
        "history_reconstruction_consistency_percent": pct(reconstructed_events, len(events)),
        "evidence_reference_checks": len(evidence_checks),
        "evidence_reference_valid_count": sum(evidence_checks),
        "evidence_reference_validity_percent": pct(sum(evidence_checks), len(evidence_checks)),
        "resumption_decisions": len(resumption_events),
        "resumption_decisions_traceable": sum(resumption_traceable),
        "resumption_decision_traceability_percent": pct(sum(resumption_traceable), len(resumption_events)),
        "diversion_depth_checks": len(created_diversions),
        "diversion_depth_within_limit": depth_valid,
        "maximum_depth_enforcement_percent": pct(depth_valid, len(created_diversions)),
        "deterministic_decision_checks": len(deterministic),
        "deterministic_decisions": sum(deterministic),
        "deterministic_decision_reproducibility_percent": pct(sum(deterministic), len(deterministic)),
        "locked_test_partition_evaluated": False,
        "learning_effectiveness_evaluated": False,
        "interpretation": "Technical orchestration, schema, traceability and history consistency only; no cognitive accuracy, prerequisite mastery, or learning gain is measured.",
    }
