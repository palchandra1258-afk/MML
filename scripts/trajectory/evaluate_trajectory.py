#!/usr/bin/env python3
"""Evaluate technical quality of a bounded Phase 13 trajectory run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_metrics import evaluate_records, read_jsonl, validate_artifacts  # noqa: E402
from mcp_ri.cognitive_state.state_schema import validate_cognitive_state  # noqa: E402


def evaluate(run_dir: Path, *, states_path: Path | None = None, output: Path | None = None) -> dict[str, Any]:
    history, records = validate_artifacts(run_dir)
    states = None
    if states_path is not None:
        states = {}
        for state in read_jsonl(states_path):
            validate_cognitive_state(state)
            states[state["cognitive_state_id"]] = state
    report_path = output or (run_dir / "evaluation.json")
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite evaluation report: {report_path}")
    report = evaluate_records(history, records, states)
    report["run_directory"] = str(run_dir)
    report["cognitive_states_source"] = None if states_path is None else str(states_path)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--states", type=Path, default=None,
                        help="optional Phase 11 JSONL for source evidence-reference checks")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = evaluate(args.run_dir, states_path=args.states, output=args.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
