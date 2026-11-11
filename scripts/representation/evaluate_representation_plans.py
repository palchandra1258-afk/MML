#!/usr/bin/env python3
"""Validate representation-plan outputs and report engineering coverage."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.representation.representation_schema import validate_representation_plan  # noqa: E402
from mcp_ri.cognitive_state.state_schema import validate_cognitive_state  # noqa: E402


def evaluate(input_path: Path, states_path: Path | None = None) -> dict[str, Any]:
    source_states: dict[str, dict[str, Any]] = {}
    if states_path is not None:
        with states_path.open("r", encoding="utf-8") as source_stream:
            for line in source_stream:
                if line.strip():
                    state = json.loads(line)
                    validate_cognitive_state(state)
                    source_states[state["cognitive_state_id"]] = state
    plans: dict[str, dict[str, Any]] = {}
    plan_order: dict[str, int] = {}
    action_counts: Counter[str] = Counter()
    representation_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    alternative_count = 0
    traceable_count = 0
    available_selection_count = 0
    temporal_links = 0
    preserved_context_links = 0
    source_state_matches = 0
    source_evidence_matches = 0
    source_recommendation_matches = 0
    with input_path.open("r", encoding="utf-8") as plan_stream:
        for line_number, line in enumerate(plan_stream, start=1):
            if not line.strip():
                continue
            plan = json.loads(line)
            try:
                validate_representation_plan(plan)
            except ValueError as exc:
                raise ValueError(f"{input_path}:{line_number}: {exc}") from exc
            if plan["plan_id"] in plans:
                raise ValueError(f"{input_path}:{line_number}: duplicate plan_id {plan['plan_id']}")
            plans[plan["plan_id"]] = plan
            plan_order[plan["plan_id"]] = len(plan_order)
            if states_path is not None:
                source_state = source_states.get(plan["input_references"]["cognitive_state_id"])
                if source_state is not None and (
                    source_state["learner_id"] == plan["learner_id"]
                    and source_state["state_version"] == plan["input_references"]["cognitive_state_version"]
                ):
                    source_state_matches += 1
                    source_evidence_ids = {item["evidence_id"] for item in source_state["evidence_references"]}
                    cited_ids = set(plan["input_references"]["supporting_evidence_ids"] + plan["input_references"]["contradictory_evidence_ids"])
                    if cited_ids <= source_evidence_ids:
                        source_evidence_matches += 1
                    source_recommendation_ids = {
                        item["recommendation_id"] for item in source_state["diagnostic_recommendations"]
                    }
                    if set(plan["input_references"]["diagnostic_recommendation_ids"]) <= source_recommendation_ids:
                        source_recommendation_matches += 1
            decision = plan["decision"]
            action_counts[decision["selected_action"]] += 1
            representation_counts[decision["selected_representation"] or "none"] += 1
            alternative_count += len(decision["alternative_representations"])
            if decision["selected_representation"] is not None:
                available_selection_count += 1
            if plan["input_references"]["cognitive_state_id"] and (
                plan["input_references"]["supporting_evidence_ids"]
                or plan["input_references"]["contradictory_evidence_ids"]
                or not plan["concept_grounding"]["related_skill_ids"]
            ):
                traceable_count += 1
            for rule in decision["policy_trace"]:
                if rule["conditions_satisfied"]:
                    rule_counts[rule["rule_id"]] += 1

    for plan in plans.values():
        previous_id = plan["previous_plan_id"]
        if previous_id is not None:
            temporal_links += 1
            prior = plans.get(previous_id)
            if prior is None:
                raise ValueError(f"plan {plan['plan_id']} references missing prior plan {previous_id}")
            if prior["learner_id"] != plan["learner_id"] or prior["concept_id"] != plan["concept_id"]:
                raise ValueError(f"plan {plan['plan_id']} prior link crosses learner/concept")
            if prior["plan_version"] + 1 != plan["plan_version"] or plan_order[previous_id] >= plan_order[plan["plan_id"]]:
                raise ValueError(f"plan {plan['plan_id']} prior link is not an earlier consecutive version")
            if prior["input_references"]["cognitive_state_version"] > plan["input_references"]["cognitive_state_version"]:
                raise ValueError(f"plan {plan['plan_id']} moves to an earlier cognitive-state version")
            before = prior["teaching_context"]
            after = plan["teaching_context"]
            fields = ("current_concept_id", "current_learning_objective", "current_representation", "trajectory_id", "branch_return_pointer")
            if all(before[field] == after[field] for field in fields):
                preserved_context_links += 1

    total = len(plans)
    return {
        "status": "complete",
        "input": str(input_path),
        "plans_validated": total,
        "action_counts": dict(sorted(action_counts.items())),
        "representation_counts": dict(sorted(representation_counts.items())),
        "rule_activation_counts": dict(sorted(rule_counts.items())),
        "alternative_records": alternative_count,
        "plans_with_cognitive_state_and_evidence_grounding": traceable_count,
        "traceability_rate": traceable_count / total if total else None,
        "source_cognitive_state_matches": source_state_matches if states_path is not None else None,
        "source_evidence_reference_matches": source_evidence_matches if states_path is not None else None,
        "source_diagnostic_recommendation_matches": source_recommendation_matches if states_path is not None else None,
        "source_traceability_rate": source_evidence_matches / total if states_path is not None and total else None,
        "selected_capabilities_registered_available": available_selection_count,
        "temporal_plan_links": temporal_links,
        "temporal_links_with_preserved_context": preserved_context_links,
        "locked_test_partition_evaluated": False,
        "learning_effectiveness_evaluated": False,
        "interpretation": "These are schema, traceability, rule-coverage and context-preservation checks. They do not measure representation effectiveness or learning gains.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--states", type=Path, help="Phase 11 JSONL source for independent state/evidence cross-checks")
    args = parser.parse_args()
    report = evaluate(args.input, args.states)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
