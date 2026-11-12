#!/usr/bin/env python3
"""Build bounded, validation-only Phase 11 cognitive-state snapshots."""

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

from mcp_ri.cognitive_state import CognitiveStateHistory, estimate_cognitive_state  # noqa: E402
from mcp_ri.evidence.adapters.interaction import InteractionAdapter  # noqa: E402
from mcp_ri.evidence.adapters.temporal import TemporalHistoryAdapter  # noqa: E402
from mcp_ri.evidence.evidence_schema import validate_evidence  # noqa: E402
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402


REQUIRED_COLUMNS = {
    "learner_id", "source_row_order", "timestamp", "question_id", "correctness",
    "skill_tags", "split_unseen_learner", "is_exact_duplicate",
}


def _write_line(stream, value: dict[str, Any]) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def run(
    data_path: Path,
    output_dir: Path,
    *,
    sample_learners: int,
    checkpoints: tuple[int, ...],
    max_interactions_per_learner: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=False)
    states_path = output_dir / "cognitive_states.jsonl"
    report_path = output_dir / "evaluation.json"
    adapter = InteractionAdapter()
    temporal_adapter = TemporalHistoryAdapter()
    checkpoint_set = set(checkpoints)
    max_checkpoint = max(checkpoints)
    rows_scanned = 0
    selected_learners = 0
    written_states = 0
    normalized_interactions = 0
    status_counts: Counter[str] = Counter()
    hypothesis_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    modal_counts: Counter[str] = Counter()
    current_learner: str | None = None
    accumulator: LearnerStateAccumulator | None = None
    history: CognitiveStateHistory | None = None
    current_records: list[dict[str, Any]] = []
    capture_counts: set[int] = set()
    stop_current_learner = False

    with states_path.open("x", encoding="utf-8") as output:
        def capture() -> None:
            nonlocal written_states
            assert accumulator is not None and history is not None and current_records
            phase9_state = accumulator.snapshot()
            interaction_ids = [record["evidence_id"] for record in current_records]
            temporal_record = temporal_adapter.from_learner_state(
                phase9_state,
                state_reference=f"phase9-prefix:{phase9_state['learner_id']}:{current_records[-1]['temporal']['sequence_number']}",
                related_evidence_ids=interaction_ids,
                source_file="derived:Phase9 LearnerStateAccumulator chronological prefix",
            )
            validate_evidence(temporal_record)
            evidence = [*current_records, temporal_record]
            end_sequence = current_records[-1]["temporal"]["sequence_number"]
            start_sequence = current_records[0]["temporal"]["sequence_number"]
            state = estimate_cognitive_state(
                phase9_state,
                evidence,
                sequence_start=start_sequence,
                sequence_end=end_sequence,
            )
            versioned = history.append(state)
            _write_line(output, versioned)
            written_states += 1
            for concept in versioned["concept_estimates"]:
                status_counts[concept["estimated_learning_status"]] += 1
            for hypothesis in versioned["possible_difficulty_hypotheses"]:
                hypothesis_counts[hypothesis["hypothesis_type"]] += 1
            uncertainty_counts[versioned["uncertainty"]["overall_uncertainty"]] += 1
            for modality in versioned["observed_evidence_summary"]["available_modalities"]:
                modal_counts[modality] += 1

        with gzip.open(data_path, "rt", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
            if missing:
                raise ValueError(f"processed EdNet table lacks columns: {missing}")
            for row in reader:
                rows_scanned += 1
                learner = row["learner_id"]
                if learner != current_learner:
                    if accumulator is not None and current_records:
                        last_sequence = current_records[-1]["temporal"]["sequence_number"]
                        latest_end = history.latest["observation_window"]["sequence_end"] if history and history.latest else None
                        if latest_end != last_sequence:
                            capture()
                    if selected_learners >= sample_learners:
                        break
                    current_learner = learner
                    current_records = []
                    capture_counts = set()
                    stop_current_learner = False
                    if row["split_unseen_learner"] == "validation":
                        selected_learners += 1
                        accumulator = LearnerStateAccumulator(learner)
                        history = CognitiveStateHistory(learner)
                    else:
                        accumulator = None
                        history = None

                if accumulator is None or stop_current_learner:
                    continue
                record = adapter.from_processed_row(row)
                validate_evidence(record)
                accumulator.update(row)
                current_records.append(record)
                normalized_interactions += 1
                if accumulator.labelled_responses in checkpoint_set and accumulator.labelled_responses not in capture_counts:
                    capture()
                    capture_counts.add(accumulator.labelled_responses)
                if (
                    accumulator.labelled_responses >= max_checkpoint
                    or accumulator.total_interactions >= max_interactions_per_learner
                ):
                    stop_current_learner = True

            if accumulator is not None and current_records:
                latest_end = history.latest["observation_window"]["sequence_end"] if history and history.latest else None
                if latest_end != current_records[-1]["temporal"]["sequence_number"]:
                    capture()

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "source": str(data_path),
        "partition": "split_unseen_learner=validation only",
        "locked_test_partition_evaluated": False,
        "sampling_policy": "first validation learners in processed source order; chronological prefixes captured at labeled-event checkpoints",
        "selected_learners": selected_learners,
        "state_snapshots": written_states,
        "checkpoint_labeled_responses": list(checkpoints),
        "max_interactions_per_learner": max_interactions_per_learner,
        "processed_rows_scanned": rows_scanned,
        "normalized_interaction_records": normalized_interactions,
        "concept_status_counts": dict(status_counts),
        "hypothesis_counts": dict(hypothesis_counts),
        "overall_uncertainty_counts": dict(uncertainty_counts),
        "available_modality_state_counts": dict(modal_counts),
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "output": str(states_path),
        "claims_boundary": "These are provisional behavioral rule categories. They are not validated cognitive estimates, and no cognitive ground truth is available.",
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/reports")
    parser.add_argument("--output-dir", type=Path, help="new output directory; must not already exist")
    parser.add_argument("--sample-learners", type=int, default=100)
    parser.add_argument("--checkpoints", type=int, nargs="+", default=[5, 10], help="labeled response counts at which to append state snapshots")
    parser.add_argument("--max-interactions-per-learner", type=int, default=100)
    args = parser.parse_args()
    if args.sample_learners <= 0 or args.max_interactions_per_learner <= 0:
        parser.error("sample size and per-learner event limit must be positive")
    checkpoints = tuple(sorted(set(args.checkpoints)))
    if not checkpoints or checkpoints[0] <= 0:
        parser.error("checkpoints must be positive labeled-response counts")
    data_path = args.data_root / "processed/ednet/ednet_kt1_features.csv.gz"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or args.output_root / f"phase11-cognitive-state-{stamp}"
    report = run(
        data_path,
        output_dir,
        sample_learners=args.sample_learners,
        checkpoints=checkpoints,
        max_interactions_per_learner=args.max_interactions_per_learner,
    )
    print(json.dumps({"output_dir": str(output_dir), **report}, indent=2))


if __name__ == "__main__":
    main()
