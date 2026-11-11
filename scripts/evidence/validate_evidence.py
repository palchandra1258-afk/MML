#!/usr/bin/env python3
"""Validate normalized evidence JSONL, evidence groups, and integration traces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.evidence.evidence_schema import validate_alignment, validate_evidence, validate_group  # noqa: E402


def validate_jsonl(path: Path, validator, kind: str) -> int:
    count = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                validator(value)
            except Exception as error:
                raise ValueError(f"{kind} line {line_number}: {error}") from error
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_jsonl", type=Path)
    parser.add_argument("--groups-jsonl", type=Path)
    parser.add_argument("--alignments-jsonl", type=Path)
    parser.add_argument("--integration-trace", type=Path)
    args = parser.parse_args()
    evidence_count = validate_jsonl(args.evidence_jsonl, validate_evidence, "evidence")
    group_count = validate_jsonl(args.groups_jsonl, validate_group, "group") if args.groups_jsonl else 0
    alignment_count = validate_jsonl(args.alignments_jsonl, validate_alignment, "alignment") if args.alignments_jsonl else 0
    if args.integration_trace:
        trace = json.loads(args.integration_trace.read_text(encoding="utf-8"))
        for record in trace["interaction_evidence"]:
            validate_evidence(record)
        validate_evidence(trace["temporal_history_evidence"])
    print(json.dumps({"evidence_records_validated": evidence_count, "groups_validated": group_count,
                      "alignment_candidates_validated": alignment_count,
                      "integration_trace_validated": bool(args.integration_trace)}, indent=2))


if __name__ == "__main__":
    main()
