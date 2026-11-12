#!/usr/bin/env python3
"""Build validation-only learner states and descriptive evaluation summaries."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import resource
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402
from mcp_ri.ednet_preprocessing import split_unseen_learner  # noqa: E402


REQUIRED_COLUMNS = {
    "learner_id", "source_row_order", "timestamp", "question_id", "correctness",
    "skill_tags", "split_unseen_learner", "is_exact_duplicate",
}


def _new_metrics() -> dict[str, Any]:
    return {
        "learners": 0,
        "interactions": 0,
        "labelled_responses": 0,
        "unlabelled_interactions": 0,
        "concepts": 0,
        "concept_attempts_by_bucket": Counter(),
        "concept_evidence_sufficiency": Counter(),
        "overall_evidence_sufficiency": Counter(),
        "overall_uncertainty_levels": Counter(),
        "concept_uncertainty_levels": Counter(),
        "overall_trends": Counter(),
        "concept_trends": Counter(),
        "overall_issues": Counter(),
        "concept_issues": Counter(),
        "concept_historical_accuracy_sum": 0.0,
        "concept_recent_accuracy_sum": 0.0,
        "concept_smoothed_accuracy_sum": 0.0,
        "concept_shrinkage_abs_sum": 0.0,
        "concept_shrinkage_count": 0,
        "overall_historical_accuracy_sum": 0.0,
        "overall_recent_accuracy_sum": 0.0,
        "overall_smoothed_accuracy_sum": 0.0,
        "overall_shrinkage_abs_sum": 0.0,
        "overall_shrinkage_count": 0,
        "recent_vs_historical_abs_change_sum": 0.0,
        "recent_vs_historical_compared_learners": 0,
        "states_schema_validated": 0,
        "model_prediction_available": 0,
    }


def _observe_state(metrics: dict[str, Any], state: dict[str, Any]) -> None:
    summary = state["observation_summary"]
    overall = state["learning_performance"]
    metrics["learners"] += 1
    metrics["interactions"] += summary["total_interactions"]
    metrics["labelled_responses"] += summary["labelled_responses"]
    metrics["unlabelled_interactions"] += summary["unlabelled_interactions"]
    metrics["states_schema_validated"] += 1
    metrics["overall_evidence_sufficiency"][overall["evidence_sufficiency"]] += 1
    metrics["overall_uncertainty_levels"][overall["uncertainty_level"]] += 1
    metrics["overall_trends"][overall["performance_trend"]] += 1
    for issue in overall["potential_issues"]:
        metrics["overall_issues"][issue] += 1
    if overall["historical_performance"] is not None:
        metrics["overall_historical_accuracy_sum"] += overall["historical_performance"]
        metrics["overall_smoothed_accuracy_sum"] += overall["estimated_performance"]
        metrics["overall_shrinkage_abs_sum"] += abs(
            overall["estimated_performance"] - overall["historical_performance"]
        )
        metrics["overall_shrinkage_count"] += 1
    if overall["recent_performance"] is not None and overall["historical_performance"] is not None:
        metrics["overall_recent_accuracy_sum"] += overall["recent_performance"]
        metrics["recent_vs_historical_abs_change_sum"] += abs(
            overall["recent_performance"] - overall["historical_performance"]
        )
        metrics["recent_vs_historical_compared_learners"] += 1

    for concept in state["concept_states"]:
        metrics["concepts"] += 1
        attempts = concept["attempts"]
        bucket = "0" if attempts == 0 else "1-4" if attempts < 5 else "5-19" if attempts < 20 else "20+"
        metrics["concept_attempts_by_bucket"][bucket] += 1
        metrics["concept_evidence_sufficiency"][concept["evidence_sufficiency"]] += 1
        metrics["concept_uncertainty_levels"][concept["uncertainty_level"]] += 1
        metrics["concept_trends"][concept["performance_trend"]] += 1
        for issue in concept["potential_issues"]:
            metrics["concept_issues"][issue] += 1
        if concept["historical_accuracy"] is not None:
            metrics["concept_historical_accuracy_sum"] += concept["historical_accuracy"]
            metrics["concept_smoothed_accuracy_sum"] += concept["smoothed_performance"]
            metrics["concept_shrinkage_abs_sum"] += abs(
                concept["smoothed_performance"] - concept["historical_accuracy"]
            )
            metrics["concept_shrinkage_count"] += 1
            if concept["recent_accuracy"] is not None:
                metrics["concept_recent_accuracy_sum"] += concept["recent_accuracy"]


def _mean(total: float, count: int) -> float | None:
    return total / count if count else None


def _finalize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        key: dict(metrics[key])
        for key in (
            "concept_attempts_by_bucket", "concept_evidence_sufficiency",
            "overall_evidence_sufficiency", "overall_uncertainty_levels",
            "concept_uncertainty_levels", "overall_trends", "concept_trends",
            "overall_issues", "concept_issues",
        )
    }
    result.update({
        key: metrics[key]
        for key in (
            "learners", "interactions", "labelled_responses", "unlabelled_interactions",
            "concepts", "states_schema_validated", "model_prediction_available",
        )
    })
    result["descriptive_means"] = {
        "learner_macro_historical_accuracy": _mean(
            metrics["overall_historical_accuracy_sum"], metrics["overall_shrinkage_count"]
        ),
        "learner_macro_recent_accuracy": _mean(
            metrics["overall_recent_accuracy_sum"], metrics["recent_vs_historical_compared_learners"]
        ),
        "learner_macro_smoothed_performance": _mean(
            metrics["overall_smoothed_accuracy_sum"], metrics["overall_shrinkage_count"]
        ),
        "learner_macro_absolute_beta_shrinkage": _mean(
            metrics["overall_shrinkage_abs_sum"], metrics["overall_shrinkage_count"]
        ),
        "concept_macro_historical_accuracy": _mean(
            metrics["concept_historical_accuracy_sum"], metrics["concept_shrinkage_count"]
        ),
        "concept_macro_recent_accuracy": _mean(
            metrics["concept_recent_accuracy_sum"], metrics["concept_shrinkage_count"]
        ),
        "concept_macro_smoothed_performance": _mean(
            metrics["concept_smoothed_accuracy_sum"], metrics["concept_shrinkage_count"]
        ),
        "concept_macro_absolute_beta_shrinkage": _mean(
            metrics["concept_shrinkage_abs_sum"], metrics["concept_shrinkage_count"]
        ),
    }
    result["experiments"] = {
        "A_historical_state": {
            "learners_with_labelled_responses": metrics["overall_shrinkage_count"],
            "mean_observed_historical_accuracy_across_learners": _mean(
                metrics["overall_historical_accuracy_sum"], metrics["overall_shrinkage_count"]
            ),
        },
        "B_recent_state": {
            "learners_with_recent_and_historical_estimates": metrics["recent_vs_historical_compared_learners"],
            "mean_absolute_recent_minus_historical_accuracy": _mean(
                metrics["recent_vs_historical_abs_change_sum"], metrics["recent_vs_historical_compared_learners"]
            ),
        },
        "C_bayesian_smoothing": {
            "prior": {"distribution": "Beta", "alpha": 1.0, "beta": 1.0},
            "mean_absolute_shrinkage_over_learners": _mean(
                metrics["overall_shrinkage_abs_sum"], metrics["overall_shrinkage_count"]
            ),
            "mean_absolute_shrinkage_over_concepts": _mean(
                metrics["concept_shrinkage_abs_sum"], metrics["concept_shrinkage_count"]
            ),
            "concept_observation_buckets": dict(metrics["concept_attempts_by_bucket"]),
        },
        "D_temporal_change": {
            "trend_threshold_absolute_accuracy_change": 0.10,
            "trend_requires_at_least_10_labeled_observations": True,
            "learner_trend_counts": dict(metrics["overall_trends"]),
            "concept_trend_counts": dict(metrics["concept_trends"]),
        },
        "E_evidence_sufficiency": {
            "learner_evidence_counts": dict(metrics["overall_evidence_sufficiency"]),
            "concept_evidence_counts": dict(metrics["concept_evidence_sufficiency"]),
            "learner_uncertainty_counts": dict(metrics["overall_uncertainty_levels"]),
            "concept_uncertainty_counts": dict(metrics["concept_uncertainty_levels"]),
        },
    }
    result["direct_cognitive_state_accuracy"] = None
    result["direct_cognitive_state_accuracy_reason"] = (
        "No ground-truth cognitive-state, understanding, misconception, or representation-mismatch labels exist in this dataset."
    )
    result["prediction_calibration_evaluation"] = {
        "performed": False,
        "reason": "Existing prediction artifacts could not be loaded because this interpreter lacks joblib, scikit-learn, XGBoost, and PyTorch; no predictions were fabricated.",
    }
    return result


def _write_state(stream, state: dict[str, Any], metrics: dict[str, Any]) -> None:
    json.dump(state, stream, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    stream.write("\n")
    _observe_state(metrics, state)


def run(data_path: Path, output_dir: Path, max_validation_learners: int | None = None) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output_dir}")
    if not data_path.is_file():
        raise FileNotFoundError(data_path)
    output_dir.mkdir(parents=True, exist_ok=False)
    states_path = output_dir / "validation_learner_states.jsonl"
    started = time.monotonic()
    metrics = _new_metrics()
    rows_scanned = 0
    validation_interaction_rows = 0
    completed_ids: set[str] = set()
    current_id: str | None = None
    current: LearnerStateAccumulator | None = None
    current_split: str | None = None
    truncated = False
    summary_path = data_path.parent / "ednet_preprocessing_summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(summary_path)
    seed = int(json.loads(summary_path.read_text(encoding="utf-8"))["seed"])

    with gzip.open(data_path, "rt", encoding="utf-8", newline="") as source, states_path.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("processed dataset has no CSV header")
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"processed dataset missing required fields: {sorted(missing)}")
        for row in reader:
            learner_id = row["learner_id"]
            if current_id != learner_id:
                if learner_id in completed_ids:
                    raise ValueError(f"learner rows are not contiguous: {learner_id}")
                if current is not None:
                    _write_state(target, current.snapshot(), metrics)
                    completed_ids.add(current_id or "")
                    if max_validation_learners and metrics["learners"] >= max_validation_learners:
                        truncated = True
                        break
                current_id = learner_id
                current_split = split_unseen_learner(learner_id, seed)
                current = LearnerStateAccumulator(learner_id) if current_split == "validation" else None
            rows_scanned += 1
            if rows_scanned and rows_scanned % 5_000_000 == 0:
                print(
                    f"Scanned {rows_scanned:,} interactions; "
                    f"emitted {metrics['learners']:,} validation learner states",
                    flush=True,
                )
            recorded_split = row.get("split_unseen_learner", "")
            if recorded_split and recorded_split != current_split:
                raise ValueError(f"stored split disagrees with deterministic learner assignment for {learner_id}")
            if current is not None:
                current.update(row)
                validation_interaction_rows += 1
        else:
            if current is not None:
                _write_state(target, current.snapshot(), metrics)
                completed_ids.add(current_id or "")

    report = {
        "experiment_id": output_dir.name,
        "status": "partial_smoke_run" if truncated else "complete",
        "target_partition": "split_unseen_learner=validation only",
        "locked_test_partition_read_for_labels_or_state": False,
        "input": str(data_path),
        "input_bytes": data_path.stat().st_size,
        "rows_scanned": rows_scanned,
        "validation_interaction_rows_seen": validation_interaction_rows,
        "validation_partition_seed": seed,
        "max_validation_learners": max_validation_learners,
        "streaming": "one CSV pass; only one learner accumulator retained at a time",
        "metrics": _finalize_metrics(metrics),
        "runtime_seconds": time.monotonic() - started,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "outputs": {"states_jsonl": str(states_path), "evaluation_json": str(output_dir / "evaluation.json")},
        "claims_boundary": "These are behavioral response summaries. No cognitive-state ground truth or next-response model prediction was available in this environment.",
    }
    with (output_dir / "evaluation.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    with (output_dir / "run.json").open("w", encoding="utf-8") as stream:
        json.dump({key: report[key] for key in ("experiment_id", "status", "target_partition", "locked_test_partition_read_for_labels_or_state", "input", "rows_scanned", "validation_interaction_rows_seen", "runtime_seconds", "peak_process_rss_kib", "outputs")}, stream, indent=2)
        stream.write("\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(os.environ.get("MCP_RI_DATA_DIR", ROOT / "data")))
    parser.add_argument("--output-dir", type=Path, help="new output directory; refuses overwrite")
    parser.add_argument("--max-validation-learners", type=int, help="optional bounded smoke run")
    args = parser.parse_args()
    if args.max_validation_learners is not None and args.max_validation_learners <= 0:
        parser.error("--max-validation-learners must be positive")
    data_path = args.data_root.expanduser() / "processed/ednet/ednet_kt1_features.csv.gz"
    if args.output_dir:
        output_dir = args.output_dir.expanduser()
    else:
        run_id = datetime.now(timezone.utc).strftime("phase9-learner-state-%Y%m%dT%H%M%SZ")
        output_dir = ROOT / "results/reports" / run_id
    report = run(data_path, output_dir, args.max_validation_learners)
    print(json.dumps({
        "status": report["status"],
        "output_dir": str(output_dir),
        "rows_scanned": report["rows_scanned"],
        "validation_interaction_rows": report["validation_interaction_rows_seen"],
        "validation_learners": report["metrics"]["learners"],
        "runtime_seconds": report["runtime_seconds"],
        "peak_process_rss_kib": report["peak_process_rss_kib"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
