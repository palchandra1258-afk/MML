#!/usr/bin/env python3
"""Print a concise decision audit for one plan_id in a JSONL file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("plan_id")
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as stream:
        for line in stream:
            plan = json.loads(line)
            if plan.get("plan_id") == args.plan_id:
                print(json.dumps({
                    "plan_id": plan["plan_id"],
                    "learner_id": plan["learner_id"],
                    "concept_id": plan["concept_id"],
                    "cognitive_state_id": plan["input_references"]["cognitive_state_id"],
                    "selected_representation": plan["decision"]["selected_representation"],
                    "selected_action": plan["decision"]["selected_action"],
                    "delivery_status": plan["decision"]["delivery_status"],
                    "decision_reason": plan["decision"]["decision_reason"],
                    "policy_trace": plan["decision"]["policy_trace"],
                    "alternatives": plan["decision"]["alternative_representations"],
                    "limitations": plan["limitations"],
                    "teaching_context": plan["teaching_context"],
                }, indent=2))
                return
    raise SystemExit(f"plan_id not found: {args.plan_id}")


if __name__ == "__main__":
    main()
