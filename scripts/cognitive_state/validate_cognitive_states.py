#!/usr/bin/env python3
"""Stream-validate cognitive-state JSONL and per-learner version links."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.cognitive_state.state_schema import validate_cognitive_state  # noqa: E402


def validate_jsonl(path: Path) -> dict[str, object]:
    latest: dict[str, dict[str, object]] = {}
    seen_state_ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    hypothesis_counts: Counter[str] = Counter()
    state_count = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                state = json.loads(line)
                validate_cognitive_state(state)
                state_id = state["cognitive_state_id"]
                learner_id = state["learner_id"]
                if state_id in seen_state_ids:
                    raise ValueError("duplicate cognitive_state_id")
                prior = latest.get(learner_id)
                if prior is None:
                    if state["state_version"] != 1 or state["previous_state_id"] is not None:
                        raise ValueError("first learner state must start at version 1")
                else:
                    if state["state_version"] != prior["state_version"] + 1:
                        raise ValueError("state_version is not consecutive")
                    if state["previous_state_id"] != prior["cognitive_state_id"]:
                        raise ValueError("previous_state_id does not match preceding learner state")
                    old_end = prior["observation_window"]["sequence_end"]
                    new_end = state["observation_window"]["sequence_end"]
                    if old_end is not None and new_end is not None and new_end < old_end:
                        raise ValueError("sequence_end decreases across learner versions")
                seen_state_ids.add(state_id)
                latest[learner_id] = state
                state_count += 1
                for estimate in state["concept_estimates"]:
                    status_counts[estimate["estimated_learning_status"]] += 1
                for hypothesis in state["possible_difficulty_hypotheses"]:
                    hypothesis_counts[hypothesis["hypothesis_type"]] += 1
            except Exception as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
    return {
        "states_validated": state_count,
        "learners": len(latest),
        "concept_status_counts": dict(status_counts),
        "hypothesis_counts": dict(hypothesis_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("states_jsonl", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_jsonl(args.states_jsonl), indent=2))


if __name__ == "__main__":
    main()
