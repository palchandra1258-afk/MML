#!/usr/bin/env python3
"""Train/evaluate EdNet response baselines without loading the CSV into RAM."""

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

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import SGDClassifier

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.models.ednet_logistic import (  # noqa: E402
    SparseFeatureEncoder,
    classification_metrics,
    row_is_training_sample,
    assert_training_feature_whitelist,
)


def read_chunks(dataset: Path, *, predicate, batch_size: int):
    with gzip.open(dataset, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "correctness" not in reader.fieldnames:
            raise ValueError("processed CSV is missing the correctness column/header")
        batch = []
        for row in reader:
            if not predicate(row):
                continue
            batch.append(row)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def fit_encoder(dataset: Path, *, seed: int, sample_percent: int, batch_size: int):
    encoder = SparseFeatureEncoder()
    counts = Counter()
    sampled_learners: set[str] = set()
    t0 = time.monotonic()

    def selected(row):
        return row_is_training_sample(row, seed=seed, sample_percent=sample_percent)

    for batch in read_chunks(dataset, predicate=selected, batch_size=batch_size):
        encoder.fit_batch(batch)
        counts["examples"] += len(batch)
        sampled_learners.update(row["learner_id"] for row in batch)
        counts["correct"] += sum(row["correctness"] == "1" for row in batch)
        counts["incorrect"] += sum(row["correctness"] == "0" for row in batch)
        if counts["examples"] and counts["examples"] % 500_000 < len(batch):
            print(f"Encoder fit: {counts['examples']:,} sampled training rows", flush=True)
    if counts["examples"] == 0 or counts["correct"] == 0 or counts["incorrect"] == 0:
        raise ValueError("the deterministic training sample must contain both target classes")
    encoder.finalize()
    counts["learners"] = len(sampled_learners)
    counts["seconds"] = time.monotonic() - t0
    return encoder, dict(counts)


def train_model(dataset: Path, encoder: SparseFeatureEncoder, *, seed: int, sample_percent: int, batch_size: int, epochs: int):
    model = SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=1e-5,
        learning_rate="optimal",
        max_iter=1,
        tol=None,
        shuffle=True,
        average=True,
        random_state=seed,
    )
    timings = []
    total_examples = 0
    total_correct = 0
    total_incorrect = 0
    for epoch in range(epochs):
        start = time.monotonic()

        def selected(row):
            return row_is_training_sample(row, seed=seed, sample_percent=sample_percent)

        epoch_rows = 0
        for batch in read_chunks(dataset, predicate=selected, batch_size=batch_size):
            x, _ = encoder.transform(batch)
            y = np.fromiter((int(row["correctness"]) for row in batch), dtype=np.int8, count=len(batch))
            model.partial_fit(x, y, classes=np.array([0, 1], dtype=np.int8))
            epoch_rows += len(batch)
            if epoch_rows and epoch_rows % 500_000 < len(batch):
                print(f"Epoch {epoch + 1}/{epochs}: trained {epoch_rows:,} rows", flush=True)
        if epoch_rows != total_examples and epoch == 0:
            total_examples = epoch_rows
        if epoch_rows != total_examples:
            raise ValueError(f"sample size changed between epochs: {total_examples} vs {epoch_rows}")
        timings.append(time.monotonic() - start)
    return model, {"examples_per_epoch": total_examples, "epoch_seconds": timings, "total_seconds": sum(timings)}


def evaluate_validation(dataset: Path, encoder: SparseFeatureEncoder, model, *, prior: float, batch_size: int):
    expected = 0
    results = {name: [] for name in ("majority", "last_response", "historical_accuracy", "sgd_logistic")}
    labels = []
    unknown = Counter()

    def validation(row):
        return row.get("split_unseen_learner") == "validation" and row.get("correctness") in {"0", "1"}

    started = time.monotonic()
    for batch in read_chunks(dataset, predicate=validation, batch_size=batch_size):
        y = np.fromiter((int(row["correctness"]) for row in batch), dtype=np.int8, count=len(batch))
        x, unknown_batch = encoder.transform(batch)
        unknown.update(unknown_batch)
        p_logistic = model.predict_proba(x)[:, 1].astype(np.float32)
        p_last = np.fromiter(
            (float(row["previous_response_correctness"]) if row.get("previous_response_correctness", "") != "" else prior for row in batch),
            dtype=np.float32, count=len(batch),
        )
        p_history = np.fromiter(
            (float(row["prior_accuracy"]) if row.get("prior_accuracy", "") != "" else prior for row in batch),
            dtype=np.float32, count=len(batch),
        )
        labels.append(y)
        results["majority"].append(np.full(len(batch), prior, dtype=np.float32))
        results["last_response"].append(p_last)
        results["historical_accuracy"].append(p_history)
        results["sgd_logistic"].append(p_logistic)
        expected += len(batch)
        if expected and expected % 1_000_000 < len(batch):
            print(f"Validation: scored {expected:,} rows", flush=True)
    y_all = np.concatenate(labels)
    metrics = {
        name: classification_metrics(y_all, np.concatenate(probabilities))
        for name, probabilities in results.items()
    }
    return metrics, expected, dict(unknown), time.monotonic() - started


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(os.environ.get("MCP_RI_DATA_DIR", ROOT / "data")))
    parser.add_argument("--output-root", type=Path, default=ROOT, help="artifact root (default: repository root)")
    parser.add_argument("--sample-percent", type=int, default=5, help="percent of training learners selected by seeded hash (default 5)")
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=20000)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.sample_percent <= 100:
        parser.error("--sample-percent must be between 1 and 100")
    if args.epochs <= 0 or args.batch_size <= 0:
        parser.error("--epochs and --batch-size must be positive")
    assert_training_feature_whitelist()

    data_root = args.data_root.expanduser()
    dataset = data_root / "processed" / "ednet" / "ednet_kt1_features.csv.gz"
    summary_path = data_root / "processed" / "ednet" / "ednet_preprocessing_summary.json"
    if not dataset.is_file() or not summary_path.is_file():
        print(f"Processed dataset or summary is missing under {data_root}", file=sys.stderr)
        return 2
    summary = json.loads(summary_path.read_text())
    output_root = args.output_root.expanduser()
    model_dir = output_root / "models"
    paths = {
        "baselines": model_dir / "baselines" / "ednet_baselines.json",
        "trained": model_dir / "trained" / "ednet_sgd_logistic.joblib",
        "preprocessor": model_dir / "preprocessing" / "ednet_sgd_preprocessor.json",
        "experiment": output_root / "results" / "reports" / "ednet_logistic_experiment.json",
        "metrics": output_root / "results" / "tables" / "ednet_validation_metrics.csv",
        "calibration": output_root / "results" / "tables" / "ednet_validation_calibration.csv",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not args.overwrite:
        print("Experiment outputs already exist; use --overwrite after reviewing them.", file=sys.stderr)
        return 2
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    start_total = time.monotonic()
    run_record = {
        "experiment": "EdNet KT1 next submitted-answer correctness; unseen-learner protocol",
        "status": "running",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_semantics": "behavioral response correctness, not a direct cognitive-state measure",
        "training_configuration": {
            "model": "sklearn.linear_model.SGDClassifier(loss='log_loss')",
            "sample_percent_of_training_learners": args.sample_percent,
            "sampling": "deterministic BLAKE2 learner hash, restricted to train learners only",
            "seed": args.seed,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "validation_split": "split_unseen_learner=validation",
            "test_split_used": False,
        },
        "artifacts": {key: str(value) for key, value in paths.items()},
    }
    paths["experiment"].write_text(json.dumps(run_record, indent=2) + "\n")
    try:
        encoder, sample_counts = fit_encoder(
            dataset, seed=args.seed, sample_percent=args.sample_percent, batch_size=args.batch_size
        )
        encoder.save(paths["preprocessor"])
        model, training = train_model(
            dataset, encoder, seed=args.seed, sample_percent=args.sample_percent,
            batch_size=args.batch_size, epochs=args.epochs,
        )
        joblib.dump(model, paths["trained"], compress=3)
        train_full = summary["split_protocols"]["unseen_learner"]["train"]
        train_prevalence = train_full["correct_targets"] / train_full["targets"]
        baseline_spec = {
            "majority": {"probability_correct": train_prevalence, "class_threshold": 0.5, "training_prevalence_source": "full unseen-learner training split"},
            "last_response": {"probability": "previous_response_correctness; training prevalence for cold start", "cold_start_probability_correct": train_prevalence},
            "historical_accuracy": {"probability": "prior_accuracy; training prevalence for cold start", "cold_start_probability_correct": train_prevalence},
        }
        paths["baselines"].write_text(json.dumps(baseline_spec, indent=2) + "\n")
        metrics, validation_count, unknown, validation_seconds = evaluate_validation(
            dataset, encoder, model, prior=train_prevalence, batch_size=args.batch_size
        )
        total_seconds = time.monotonic() - start_total
        experiment = {
            "experiment": "EdNet KT1 next submitted-answer correctness; unseen-learner protocol",
            "status": "complete",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "target_semantics": "behavioral response correctness, not a direct cognitive-state measure",
            "dataset": summary["source_archives"],
            "processed_dataset": {"path": str(dataset), "size_bytes": dataset.stat().st_size},
            "split_protocol": "split_unseen_learner; validation only; test split not evaluated or used for selection",
            "training_configuration": {
                "model": "sklearn.linear_model.SGDClassifier(loss='log_loss')",
                "scikit_learn_version": sklearn.__version__,
                "sample_percent_of_training_learners": args.sample_percent,
                "sampling": "deterministic BLAKE2 learner hash, restricted to train learners only",
                "seed": args.seed,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "alpha_l2": 1e-5,
                "learning_rate": "optimal",
                "average": True,
                "features": list(encoder.to_dict()["categorical_fields"] + encoder.to_dict()["numeric_fields"]),
                "categorical_cardinality_in_fit_sample": encoder.to_dict()["categorical_cardinality"],
                "encoded_feature_dimension": encoder.n_features,
                "excluded_whitelist_fields": ["previous_response_skill_tags"],
                "class_imbalance_handling": "none; no class weights or resampling",
                "training_sample": sample_counts,
                "full_training_split": train_full,
                "validation_examples": validation_count,
                "validation_unknown_categories": unknown,
                "epoch_training_seconds": training["epoch_seconds"],
                "training_seconds": training["total_seconds"],
                "validation_seconds": validation_seconds,
                "total_seconds": total_seconds,
                "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            },
            "metrics": metrics,
            "artifacts": {key: str(value) for key, value in paths.items()},
        }
        paths["experiment"].write_text(json.dumps(experiment, indent=2) + "\n")
        with paths["metrics"].open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["model", "accuracy", "precision_positive_correct", "recall_positive_correct", "f1_positive_correct", "roc_auc", "pr_auc_average_precision", "log_loss", "brier_score", "ece_equal_width", "n_examples"])
            for name, values in metrics.items():
                writer.writerow([name] + [values[key] for key in ("accuracy", "precision_positive_correct", "recall_positive_correct", "f1_positive_correct", "roc_auc", "pr_auc_average_precision", "log_loss", "brier_score", "ece_equal_width", "n_examples")])
        with paths["calibration"].open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["model", "lower", "upper", "count", "mean_probability", "observed_positive_rate"])
            for name, values in metrics.items():
                for item in values["calibration_bins"]:
                    writer.writerow([name, item["lower"], item["upper"], item["count"], item["mean_probability"], item["observed_positive_rate"]])
    except Exception as exc:
        run_record["status"] = "failed"
        run_record["failure"] = f"{type(exc).__name__}: {exc}"
        run_record["elapsed_seconds_before_failure"] = time.monotonic() - start_total
        paths["experiment"].write_text(json.dumps(run_record, indent=2) + "\n")
        print(f"Training experiment failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Training sample: {sample_counts['examples']:,} examples from {sample_counts['learners']:,} learners.")
    print(f"Validation examples: {validation_count:,}; outputs: {paths['experiment']}")
    for name, values in metrics.items():
        print(f"{name}: accuracy={values['accuracy']:.6f} ROC-AUC={values['roc_auc']:.6f} PR-AUC={values['pr_auc_average_precision']:.6f} log_loss={values['log_loss']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
