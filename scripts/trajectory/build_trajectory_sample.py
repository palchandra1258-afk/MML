#!/usr/bin/env python3
"""Build a bounded Phase 13 orchestration sample from Phase 11/12 references."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.cognitive_state.state_schema import validate_cognitive_state  # noqa: E402
from mcp_ri.trajectory.dependency_registry import ConceptDependencyRegistry  # noqa: E402
from mcp_ri.trajectory.diversion_detector import detect_diversion  # noqa: E402
from mcp_ri.trajectory.trajectory_builder import build_trajectory  # noqa: E402
from mcp_ri.trajectory.trajectory_manager import TrajectoryManager  # noqa: E402

DEFAULT_STATES = ROOT / "results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl"
DEFAULT_PLANS = ROOT / "results/reports/phase12-representation-20261106T112420Z/representation_plans.jsonl"


def jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("x", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
            count += 1
    return count


def load_registry(path: Path | None) -> ConceptDependencyRegistry:
    if path is None:
        return ConceptDependencyRegistry()
    document = json.loads(path.read_text(encoding="utf-8"))
    return ConceptDependencyRegistry(
        [{key: value for key, value in entry.items() if key != "schema_version"}
         for entry in document.get("dependencies", [])],
        registry_version=document.get("registry_version", 1),
        created_at=document.get("created_at"),
    )


def unique_run_dir(output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = output_root / f"phase13-trajectory-{stamp}"
    candidate, suffix = base, 1
    while candidate.exists():
        candidate = output_root / f"{base.name}-{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def build(states_path: Path, plans_path: Path | None, registry_path: Path | None,
          output_root: Path, max_trajectories: int) -> Path:
    if not states_path.is_file():
        raise FileNotFoundError(states_path)
    plan_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    if plans_path is not None:
        if not plans_path.is_file():
            raise FileNotFoundError(plans_path)
        for plan in jsonl(plans_path):
            key = (plan["input_references"]["cognitive_state_id"], plan["concept_id"])
            plan_by_key[key] = plan
    registry = load_registry(registry_path)
    manager = TrajectoryManager(dependency_registry=registry)
    decision_records = []
    created_trajectory_ids: list[str] = []
    learner_ids: set[str] = set()
    states_read = 0
    skipped_empty = 0
    run_dir = unique_run_dir(output_root)

    for state in jsonl(states_path):
        if states_read >= max_trajectories:
            break
        validate_cognitive_state(state)
        states_read += 1
        learner_ids.add(state["learner_id"])
        if not state["concept_estimates"]:
            skipped_empty += 1
            continue
        estimate = state["concept_estimates"][0]
        concept_id = estimate["concept_id"]
        plan = plan_by_key.get((state["cognitive_state_id"], concept_id))
        if plan is not None:
            target_name = plan["learning_objective"]["target_concept"]
            objective = plan["learning_objective"]["objective_text"]
            goal = objective or f"Carry forward the existing learning context for {target_name}."
        else:
            goal = f"Carry forward observed concept context for {concept_id}; the source objective is unavailable."
            objective = None
        trajectory_id = f"traj_sample_{state['cognitive_state_id'].removeprefix('cs_')}"
        created_at = state["generated_at"]
        initial = build_trajectory(
            state["learner_id"], concept_id, goal,
            target_skill_ids=[concept_id],
            learning_objectives=[] if objective is None else [objective],
            previous_representation_plan_id=None if plan is None else plan["plan_id"],
            previous_cognitive_state_id=state["cognitive_state_id"],
            supporting_evidence_ids=estimate["supporting_evidence_ids"],
            learning_history_reference=f"cognitive-state:{state['cognitive_state_id']}",
            trajectory_id=trajectory_id, created_at=created_at,
        )
        manager.create(initial)
        created_trajectory_ids.append(trajectory_id)
        active = manager.activate(trajectory_id, occurred_at=created_at)
        first_decision = detect_diversion(active, cognitive_state=state,
                                          representation_plan=plan,
                                          dependency_registry=registry)
        result = manager.evaluate(trajectory_id, cognitive_state=state,
                                  representation_plan=plan, occurred_at=created_at)
        decision_records.append({
            "trajectory_id": trajectory_id,
            "cognitive_state_id": state["cognitive_state_id"],
            "concept_id": concept_id,
            "decision": result["decision"],
            "deterministic_replay_match": first_decision == result["decision"],
            "created_diversion": result["created"],
            "diversion_id": None if result["diversion"] is None else result["diversion"]["diversion_id"],
        })

    trajectories = [manager.history.reconstruct(trajectory_id)
                    for trajectory_id in sorted(created_trajectory_ids)]
    diversions = manager.history.diversion_versions
    contexts = manager.history.context_snapshots
    events = manager.history.events
    write_jsonl(run_dir / "trajectories.jsonl", trajectories)
    write_jsonl(run_dir / "diversions.jsonl", diversions)
    write_jsonl(run_dir / "context_snapshots.jsonl", contexts)
    write_jsonl(run_dir / "history_events.jsonl", events)
    write_jsonl(run_dir / "decisions.jsonl", decision_records)
    (run_dir / "dependency_registry.json").write_text(
        json.dumps(registry.as_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "status": "complete",
        "phase": 13,
        "input_cognitive_states": str(states_path),
        "input_representation_plans": None if plans_path is None else str(plans_path),
        "dependency_registry_source": None if registry_path is None else str(registry_path),
        "synthetic_dependency_edges_included": sum(
            item["verification_status"] == "synthetic_test" for item in registry.entries),
        "cognitive_states_read": states_read,
        "learners_represented": len(learner_ids),
        "empty_states_skipped": skipped_empty,
        "trajectories_created": len(trajectories),
        "diversion_versions_created": len(diversions),
        "active_diversions": sum(item["diversion_status"] == "ACTIVE"
                                  for item in manager.history.all_diversions()),
        "decision_replay_matches": sum(item["deterministic_replay_match"] for item in decision_records),
        "decision_replay_count": len(decision_records),
        "locked_test_partition_evaluated": False,
        "learning_effectiveness_evaluated": False,
        "files": ["trajectories.jsonl", "diversions.jsonl", "context_snapshots.jsonl",
                  "history_events.jsonl", "decisions.jsonl", "dependency_registry.json"],
        "interpretation": "A bounded orchestration and traceability run over existing Phase 11 validation snapshots. It does not measure cognitive accuracy, prerequisite mastery, or learning improvement.",
    }
    (run_dir / "build_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", type=Path, default=DEFAULT_STATES)
    parser.add_argument("--plans", type=Path, default=DEFAULT_PLANS)
    parser.add_argument("--registry", type=Path, default=None,
                        help="optional sourced registry JSON; defaults to empty")
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/reports")
    parser.add_argument("--max-trajectories", type=int, default=100)
    args = parser.parse_args()
    if args.max_trajectories < 1:
        parser.error("--max-trajectories must be positive")
    run_dir = build(args.states, args.plans, args.registry, args.output_root, args.max_trajectories)
    print(run_dir)


if __name__ == "__main__":
    main()
