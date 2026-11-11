#!/usr/bin/env python3
"""Create a bounded, validation-only EdNet evidence sample and Phase 9 trace."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import resource
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.evidence.adapters.interaction import InteractionAdapter  # noqa: E402
from mcp_ri.evidence.adapters.temporal import TemporalHistoryAdapter  # noqa: E402
from mcp_ri.evidence.aligner import align_records  # noqa: E402
from mcp_ri.evidence.evidence_schema import validate_evidence, validate_group  # noqa: E402
from mcp_ri.evidence.grouping import group_evidence  # noqa: E402
from mcp_ri.evidence.registry import EvidenceRegistry  # noqa: E402
from mcp_ri.evidence.state_bridge import apply_interaction_evidence  # noqa: E402
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402


REQUIRED_COLUMNS = {
    "learner_id", "source_row_order", "timestamp", "question_id", "correctness",
    "skill_tags", "session_id", "is_exact_duplicate", "split_unseen_learner",
}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def run(data_path: Path, output_dir: Path, sample_size: int) -> dict[str, Any]:
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=False)
    adapter = InteractionAdapter()
    rows_sample: list[dict[str, str]] = []
    sampled_learners: set[str] = set()
    integration_rows: list[dict[str, str]] | None = None
    current_learner: str | None = None
    current_rows: list[dict[str, str]] = []
    current_labelled_rows = 0
    scanned = 0

    with gzip.open(data_path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError(f"processed table missing required columns: {missing}")
        for row in reader:
            scanned += 1
            learner = row["learner_id"]
            if current_learner is not None and learner != current_learner:
                current_rows = []
                current_labelled_rows = 0
            current_learner = learner
            is_labelled_validation = (
                row["split_unseen_learner"] == "validation"
                and row["correctness"].strip() in {"0", "1"}
            )
            if is_labelled_validation and learner not in sampled_learners and len(rows_sample) < sample_size:
                rows_sample.append(row)
                sampled_learners.add(learner)
            if integration_rows is None:
                current_rows.append(row)
                if is_labelled_validation:
                    current_labelled_rows += 1
                    if current_labelled_rows == 2:
                        integration_rows = current_rows.copy()
            if len(rows_sample) >= sample_size and integration_rows is not None:
                break
    if len(rows_sample) != sample_size:
        raise RuntimeError(f"requested {sample_size} validation rows but found {len(rows_sample)}")
    if not integration_rows:
        raise RuntimeError("no validation learner with two labeled interactions found in scanned data")

    records = [adapter.from_processed_row(row) for row in rows_sample]
    for row, record in zip(rows_sample, records):
        expected_skills = [f"ednet_skill:{item}" for item in row["skill_tags"].split(";") if item and item != "-1"]
        expected_skills = list(dict.fromkeys(expected_skills))
        assert record["learner_id"] == row["learner_id"]
        assert record["content"]["question_id"] == row["question_id"]
        assert record["temporal"]["event_timestamp"] == row["timestamp"]
        assert record["content"]["correctness"] == int(row["correctness"])
        assert record["content"]["skill_ids"] == expected_skills
        assert record["provenance"]["source_file"].endswith(f"KT1/{row['learner_id']}.csv")
        assert record["provenance"]["source_record_id"] == f"{row['learner_id']}:{row['source_row_order']}"
        validate_evidence(record)

    registry = EvidenceRegistry()
    for record in records:
        registry.add(record)
    records = registry.records
    alignment_candidates = align_records(records)
    groups = group_evidence(records, alignment_candidates=alignment_candidates)
    for group in groups:
        validate_group(group)

    prior_row, new_row = integration_rows[-2], integration_rows[-1]
    prior_evidence = adapter.from_processed_row(prior_row)
    new_evidence = adapter.from_processed_row(new_row)
    accumulator = LearnerStateAccumulator(new_evidence["learner_id"])
    for historical_row in integration_rows[:-1]:
        accumulator.update(historical_row)
    before = accumulator.snapshot()
    after = apply_interaction_evidence(accumulator, new_evidence)
    temporal = TemporalHistoryAdapter().from_learner_state(
        after,
        state_reference=f"phase9-in-memory-validation-sample:{new_evidence['learner_id']}:{new_evidence['temporal']['sequence_number']}",
        related_evidence_ids=[prior_evidence["evidence_id"], new_evidence["evidence_id"]],
        source_file="derived:Phase9 LearnerStateAccumulator snapshot",
    )
    integration_trace = {
        "partition": "split_unseen_learner=validation",
        "learner_id": new_evidence["learner_id"],
        "interaction_evidence": [prior_evidence, new_evidence],
        "history_rows_replayed_before_new_event": len(integration_rows) - 1,
        "temporal_history_evidence": temporal,
        "state_before_new_event": before,
        "state_after_new_event": after,
        "counts": {
            "interactions_before": before["observation_summary"]["total_interactions"],
            "interactions_after": after["observation_summary"]["total_interactions"],
            "labelled_before": before["learning_performance"]["attempts"],
            "labelled_after": after["learning_performance"]["attempts"],
            "correct_before": before["learning_performance"]["correct"],
            "correct_after": after["learning_performance"]["correct"],
        },
    }
    _write_jsonl(output_dir / "interaction_evidence.jsonl", records)
    _write_jsonl(output_dir / "evidence_groups.jsonl", groups)
    _write_jsonl(output_dir / "alignment_candidates.jsonl", alignment_candidates)
    _write_json(output_dir / "phase9_integration_trace.json", integration_trace)

    basis_counts = Counter(group["grouping_basis"] for group in groups)
    link_counts = Counter(link["alignment_type"] for link in alignment_candidates)
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dataset": "EdNet-KT1 processed interaction table",
        "source_path": str(data_path),
        "partition_filter": "split_unseen_learner == validation and correctness in {0,1}",
        "sampling_policy": "first labeled validation interaction per distinct learner in processed source order; coverage sample, not population estimate",
        "locked_test_partition_evaluated": False,
        "rows_scanned_until_bounded_sample_complete": scanned,
        "interaction_evidence_records": len(records),
        "evidence_schema_validated": len(records),
        "sample_provenance_checks_passed": len(records),
        "unique_learners": len({record["learner_id"] for record in records}),
        "evidence_groups": len(groups),
        "alignment_candidates": len(alignment_candidates),
        "grouping_basis_counts": dict(basis_counts),
        "alignment_link_counts": dict(link_counts),
        "possible_duplicate_records_retained": sum(bool(record["duplicate_candidates"]) for record in registry.records),
        "phase9_integration": {
            "learner_id": new_evidence["learner_id"],
            "prior_interaction_evidence_id": prior_evidence["evidence_id"],
            "new_interaction_evidence_id": new_evidence["evidence_id"],
            "temporal_history_evidence_id": temporal["evidence_id"],
            "source_row_orders": [prior_evidence["temporal"]["sequence_number"], new_evidence["temporal"]["sequence_number"]],
            "event_timestamps": [prior_evidence["temporal"]["event_timestamp"], new_evidence["temporal"]["event_timestamp"]],
            "counts": integration_trace["counts"],
            "temporal_links": temporal["related_evidence_ids"],
            "history_rows_replayed_before_new_event": len(integration_rows) - 1,
        },
        "runtime_seconds": round(time.perf_counter() - start, 3),
        "max_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2),
    }
    _write_json(output_dir / "experiment_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/reports")
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--output-dir", type=Path, help="explicit new output directory; it must not already exist")
    args = parser.parse_args()
    if args.sample_size <= 0:
        parser.error("--sample-size must be positive")
    data_path = args.data_root / "processed/ednet/ednet_kt1_features.csv.gz"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or args.output_root / f"phase10-evidence-{stamp}"
    report = run(data_path, output_dir, args.sample_size)
    print(json.dumps({"output_dir": str(output_dir), **report}, indent=2))


if __name__ == "__main__":
    main()
