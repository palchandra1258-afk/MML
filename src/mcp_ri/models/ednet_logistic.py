"""Sparse, train-only categorical encoding and evaluation for EdNet baselines."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ..ednet_preprocessing import assert_no_target_leakage


CATEGORICAL_FIELDS = ("current_question_id", "current_part", "current_skill_tags")
NUMERIC_FIELDS = (
    "n_prior_logged_events",
    "n_prior_answered_attempts",
    "n_prior_correct",
    "prior_accuracy",
    "recent_5_accuracy",
    "recent_10_accuracy",
    "recent_accuracy_trend_5",
    "previous_response_correctness",
    "previous_elapsed_time_ms",
    "gap_since_previous_question_ms",
    "prior_skill_tag_attempts",
    "prior_skill_tag_correct",
    "prior_skill_tag_accuracy",
)
LOG_NUMERIC_FIELDS = frozenset({
    "n_prior_logged_events", "n_prior_answered_attempts", "n_prior_correct",
    "previous_elapsed_time_ms", "gap_since_previous_question_ms",
    "prior_skill_tag_attempts", "prior_skill_tag_correct",
})
USED_FEATURES = (*CATEGORICAL_FIELDS, *NUMERIC_FIELDS)
FORBIDDEN_INPUTS = frozenset({
    "correctness", "submitted_answer", "correct_answer", "elapsed_time_ms",
    "split_unseen_learner", "split_future_known_learner", "learner_id",
    "source_row_order", "timestamp", "session_id", "source_dataset", "is_exact_duplicate",
})


def assert_training_feature_whitelist() -> None:
    assert_no_target_leakage()
    overlap = FORBIDDEN_INPUTS.intersection(USED_FEATURES)
    if overlap:
        raise ValueError(f"forbidden fields included in training features: {sorted(overlap)}")


def row_is_training_sample(row: Mapping[str, str], *, seed: int, sample_percent: int) -> bool:
    if row.get("split_unseen_learner") != "train" or row.get("correctness") not in {"0", "1"}:
        return False
    return _sample_bucket(row.get("learner_id", ""), seed) < sample_percent * 100


def _sample_bucket(learner_id: str, seed: int) -> int:
    import hashlib

    digest = hashlib.blake2b(
        f"ednet-logistic-subset:{seed}:{learner_id}".encode("utf-8"),
        digest_size=8,
        person=b"mcp-ri-samp",
    ).digest()
    return int.from_bytes(digest, "big") % 10_000


def _number(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _numeric_value(field: str, raw: Any) -> float | None:
    value = _number(raw)
    if value is None:
        return None
    if field in LOG_NUMERIC_FIELDS:
        if value < 0:
            return None
        return math.log1p(value)
    return value


def _tags(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(dict.fromkeys(tag.strip() for tag in str(value).split(";") if tag.strip() and tag.strip() != "-1"))


class SparseFeatureEncoder:
    """One-hot item/part/tag features plus train-standardized numeric features."""

    def __init__(self) -> None:
        self.question_ids: set[str] = set()
        self.parts: set[str] = set()
        self.skill_tags: set[str] = set()
        self.count = np.zeros(len(NUMERIC_FIELDS), dtype=np.int64)
        self.mean = np.zeros(len(NUMERIC_FIELDS), dtype=np.float64)
        self.m2 = np.zeros(len(NUMERIC_FIELDS), dtype=np.float64)
        self.question_index: dict[str, int] = {}
        self.part_index: dict[str, int] = {}
        self.tag_index: dict[str, int] = {}
        self.missing_numeric_counts = np.zeros(len(NUMERIC_FIELDS), dtype=np.int64)
        self.fitted = False

    def fit_batch(self, rows: Iterable[Mapping[str, str]]) -> int:
        if self.fitted:
            raise RuntimeError("encoder is already finalized")
        batch_numeric: list[list[float]] = []
        for row in rows:
            qid = row.get("current_question_id", "")
            part = row.get("current_part", "")
            if qid:
                self.question_ids.add(qid)
            if part:
                self.parts.add(part)
            self.skill_tags.update(_tags(row.get("current_skill_tags", "")))
            numeric_row = []
            for field in NUMERIC_FIELDS:
                value = _numeric_value(field, row.get(field))
                numeric_row.append(np.nan if value is None else value)
            batch_numeric.append(numeric_row)
        if not batch_numeric:
            return 0
        matrix = np.asarray(batch_numeric, dtype=np.float64)
        batch_count = np.isfinite(matrix).sum(axis=0).astype(np.int64)
        self.missing_numeric_counts += len(batch_numeric) - batch_count
        for column, n in enumerate(batch_count):
            if n == 0:
                continue
            values = matrix[np.isfinite(matrix[:, column]), column]
            batch_mean = float(values.mean())
            batch_m2 = float(np.square(values - batch_mean).sum())
            old_n = int(self.count[column])
            if old_n == 0:
                self.count[column] = n
                self.mean[column] = batch_mean
                self.m2[column] = batch_m2
            else:
                delta = batch_mean - self.mean[column]
                new_n = old_n + int(n)
                self.mean[column] += delta * int(n) / new_n
                self.m2[column] += batch_m2 + delta * delta * old_n * int(n) / new_n
                self.count[column] = new_n
        return len(batch_numeric)

    def finalize(self) -> None:
        if self.fitted:
            return
        self.question_index = {value: i for i, value in enumerate(sorted(self.question_ids))}
        self.part_index = {value: i for i, value in enumerate(sorted(self.parts))}
        self.tag_index = {value: i for i, value in enumerate(sorted(self.skill_tags))}
        self.std = np.sqrt(np.divide(self.m2, self.count, out=np.ones_like(self.m2), where=self.count > 0))
        self.std[self.std == 0] = 1.0
        self.fitted = True

    @property
    def categorical_dimensions(self) -> int:
        return len(self.question_index) + 1 + len(self.part_index) + 1 + len(self.tag_index) + 2

    @property
    def n_features(self) -> int:
        return self.categorical_dimensions + 2 * len(NUMERIC_FIELDS)

    def transform(self, rows: list[Mapping[str, str]]):
        if not self.fitted:
            raise RuntimeError("call finalize() before transform")
        indices: list[int] = []
        data: list[float] = []
        indptr = [0]
        unknown = Counter()
        q_base = 0
        part_base = len(self.question_index) + 1
        tag_base = part_base + len(self.part_index) + 1
        numeric_base = self.categorical_dimensions
        for row in rows:
            qid = row.get("current_question_id", "")
            if qid in self.question_index:
                indices.append(q_base + self.question_index[qid])
            else:
                indices.append(q_base + len(self.question_index))
                unknown["question_id"] += 1
            data.append(1.0)

            part = row.get("current_part", "")
            if part in self.part_index:
                indices.append(part_base + self.part_index[part])
            else:
                indices.append(part_base + len(self.part_index))
                unknown["part"] += 1
            data.append(1.0)

            tags = _tags(row.get("current_skill_tags", ""))
            if not tags:
                indices.append(tag_base + len(self.tag_index) + 1)
                data.append(1.0)
            else:
                found = False
                unknown_tag_found = False
                for tag in tags:
                    if tag in self.tag_index:
                        indices.append(tag_base + self.tag_index[tag])
                        data.append(1.0)
                        found = True
                    else:
                        unknown["skill_tag"] += 1
                        unknown_tag_found = True
                if not found:
                    indices.append(tag_base + len(self.tag_index))
                    data.append(1.0)
                elif unknown_tag_found:
                    indices.append(tag_base + len(self.tag_index))
                    data.append(1.0)

            numeric_values: list[float] = []
            missing_values: list[float] = []
            for field_index, field in enumerate(NUMERIC_FIELDS):
                value = _numeric_value(field, row.get(field))
                if value is None:
                    numeric_values.append(0.0)
                    missing_values.append(1.0)
                else:
                    numeric_values.append((value - self.mean[field_index]) / self.std[field_index])
                    missing_values.append(0.0)
            for feature_index, value in enumerate(numeric_values):
                if value != 0:
                    indices.append(numeric_base + feature_index)
                    data.append(value)
            missing_base = numeric_base + len(NUMERIC_FIELDS)
            for feature_index, value in enumerate(missing_values):
                if value:
                    indices.append(missing_base + feature_index)
                    data.append(1.0)
            indptr.append(len(indices))
        matrix = csr_matrix(
            (np.asarray(data, dtype=np.float64), np.asarray(indices, dtype=np.int32), np.asarray(indptr, dtype=np.int32)),
            shape=(len(rows), self.n_features),
        )
        return matrix, dict(unknown)

    def to_dict(self) -> dict[str, Any]:
        if not self.fitted:
            raise RuntimeError("cannot serialize an unfitted encoder")
        return {
            "categorical_fields": list(CATEGORICAL_FIELDS),
            "numeric_fields": list(NUMERIC_FIELDS),
            "excluded_feature_whitelist_fields": ["previous_response_skill_tags"],
            "question_ids": sorted(self.question_index),
            "parts": sorted(self.part_index),
            "skill_tags": sorted(self.tag_index),
            "numeric_mean_after_log_transform": self.mean.tolist(),
            "numeric_std_after_log_transform": self.std.tolist(),
            "numeric_observed_counts": self.count.tolist(),
            "numeric_missing_counts_in_fit_sample": self.missing_numeric_counts.tolist(),
            "categorical_cardinality": {
                "current_question_id": len(self.question_index),
                "current_part": len(self.part_index),
                "current_skill_tag": len(self.tag_index),
            },
            "one_hot_unknown_buckets": True,
            "numeric_imputation": "train mean, yielding scaled zero, plus an explicit missing indicator",
            "n_features": self.n_features,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SparseFeatureEncoder":
        encoder = cls()
        encoder.question_index = {key: i for i, key in enumerate(value["question_ids"])}
        encoder.part_index = {key: i for i, key in enumerate(value["parts"])}
        encoder.tag_index = {key: i for i, key in enumerate(value["skill_tags"])}
        encoder.question_ids = set(encoder.question_index)
        encoder.parts = set(encoder.part_index)
        encoder.skill_tags = set(encoder.tag_index)
        encoder.mean = np.asarray(value["numeric_mean_after_log_transform"], dtype=np.float64)
        encoder.std = np.asarray(value["numeric_std_after_log_transform"], dtype=np.float64)
        encoder.count = np.asarray(value["numeric_observed_counts"], dtype=np.int64)
        encoder.missing_numeric_counts = np.asarray(value["numeric_missing_counts_in_fit_sample"], dtype=np.int64)
        encoder.m2 = np.square(encoder.std) * encoder.count
        encoder.fitted = True
        return encoder

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n")

    @classmethod
    def load(cls, path: Path) -> "SparseFeatureEncoder":
        return cls.from_dict(json.loads(path.read_text()))


def classification_metrics(y_true: np.ndarray, y_probability: np.ndarray, *, bins: int = 15):
    y_true = np.asarray(y_true, dtype=np.int8)
    y_probability = np.clip(np.asarray(y_probability, dtype=np.float64), 1e-15, 1 - 1e-15)
    y_pred = (y_probability >= 0.5).astype(np.int8)
    counts = np.bincount(y_true, minlength=2)
    calibration = []
    ece = 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    for index in range(bins):
        if index == bins - 1:
            mask = (y_probability >= edges[index]) & (y_probability <= edges[index + 1])
        else:
            mask = (y_probability >= edges[index]) & (y_probability < edges[index + 1])
        n = int(mask.sum())
        if n:
            avg_prob = float(y_probability[mask].mean())
            observed = float(y_true[mask].mean())
            ece += n / len(y_true) * abs(avg_prob - observed)
        else:
            avg_prob, observed = None, None
        calibration.append({"lower": float(edges[index]), "upper": float(edges[index + 1]), "count": n, "mean_probability": avg_prob, "observed_positive_rate": observed})
    return {
        "n_examples": int(len(y_true)),
        "class_counts": {"incorrect_0": int(counts[0]), "correct_1": int(counts[1])},
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_positive_correct": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall_positive_correct": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_positive_correct": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_probability)),
        "pr_auc_average_precision": float(average_precision_score(y_true, y_probability)),
        "confusion_matrix_true_rows_pred_columns_labels_0_1": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "log_loss": float(log_loss(y_true, y_probability, labels=[0, 1])),
        "brier_score": float(np.mean(np.square(y_probability - y_true))),
        "ece_equal_width": float(ece),
        "calibration_bins": calibration,
    }

