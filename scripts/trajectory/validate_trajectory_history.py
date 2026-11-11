#!/usr/bin/env python3
"""Validate exported Phase 13 schemas, append-only links and reconstructions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_metrics import validate_artifacts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    history, records = validate_artifacts(args.run_dir)
    result = {
        "status": "valid",
        "trajectory_records": len(records["trajectories"]),
        "history_events": len(records["events"]),
        "diversion_versions": len(records["diversions"]),
        "context_snapshots": len(records["contexts"]),
        "trajectory_versions_reconstructed": len({
            (event["trajectory_id"], event["trajectory_version"]) for event in records["events"]
        }),
    }
    output = args.output or (args.run_dir / "history_validation.json")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite history validation report: {output}")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
