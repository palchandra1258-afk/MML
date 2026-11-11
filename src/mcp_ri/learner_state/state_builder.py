"""Streaming chronological updates for transparent behavioral learner states."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from typing import Any, Iterable, Mapping

from .state_schema import validate_state


RECENT_OVERALL_WINDOW = 10
RECENT_CONCEPT_WINDOW = 5
TREND_HALF_WINDOW = 5
TREND_THRESHOLD = 0.10
MIN_EVIDENCE_FOR_TREND = 10
BETA_PRIOR_ALPHA = 1.0
BETA_PRIOR_BETA = 1.0

LIMITATIONS = [
    "Correctness and interaction history are behavioral observations, not direct measurements of cognition or understanding.",
    "Skill tags are item metadata; they are not a validated concept ontology or misconception label.",
    "Confidence categories summarize evidence volume and a Wilson interval; they are not calibrated probabilities of learner understanding.",
    "EdNet timestamps are shifted and denote question-given times; state timestamps preserve this source time and do not identify response submission time.",
    "Preserved exact duplicate rows are counted as separate observations, matching the preprocessing policy.",
]


def skill_ids(raw: Any) -> tuple[str, ...]:
    """Return stable, unique EdNet skill identifiers; blank and -1 mean absent."""
    if raw is None:
        return ()
    values = str(raw).strip()
    if not values or values == "-1":
        return ()
    return tuple(dict.fromkeys(
        f"ednet_skill:{tag.strip()}"
        for tag in values.split(";")
        if tag.strip() and tag.strip() != "-1"
    ))


def _parse_label(raw: Any) -> int | None:
    value = "" if raw is None else str(raw).strip()
    return int(value) if value in {"0", "1"} else None


def _parse_timestamp(raw: Any) -> tuple[str | None, int | None]:
    value = "" if raw is None else str(raw).strip()
    if not value:
        return None, None
    try:
        numeric = int(value)
    except ValueError:
        return value, None
    return value, numeric


def wilson_interval(correct: int, attempts: int, z: float = 1.959963984540054) -> list[float]:
    """Wilson score interval for a binomial proportion; [0,1] with no evidence."""
    if attempts <= 0:
        return [0.0, 1.0]
    p = correct / attempts
    z2 = z * z
    denom = 1.0 + z2 / attempts
    center = (p + z2 / (2.0 * attempts)) / denom
    margin = z * math.sqrt((p * (1.0 - p) / attempts) + z2 / (4.0 * attempts * attempts)) / denom
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _evidence_labels(attempts: int, interval: list[float]) -> tuple[str, str, str, list[str]]:
    width = interval[1] - interval[0]
    if attempts == 0:
        evidence, confidence, level = "none", "low", "high"
        reasons = ["no_labelled_responses", "uncertainty_interval_spans_full_range"]
    elif attempts < 5:
        evidence, confidence, level = "low", "low", "high"
        reasons = ["few_labelled_responses"]
    elif attempts < 20:
        evidence = "moderate"
        confidence = "moderate" if width <= 0.35 else "low"
        level = "medium" if width <= 0.35 else "high"
        reasons = [] if width <= 0.35 else ["wide_wilson_interval"]
    else:
        evidence = "high"
        confidence = "high" if width <= 0.20 else "moderate"
        level = "low" if width <= 0.20 else "medium"
        reasons = [] if width <= 0.20 else ["wilson_interval_wider_than_0.20"]
    return evidence, confidence, level, reasons


def _trend(outcomes: deque[int] | list[int]) -> tuple[str, float | None]:
    values = list(outcomes)
    if len(values) < MIN_EVIDENCE_FOR_TREND:
        return "insufficient_evidence", None
    earlier = values[-2 * TREND_HALF_WINDOW:-TREND_HALF_WINDOW]
    recent = values[-TREND_HALF_WINDOW:]
    change = sum(recent) / len(recent) - sum(earlier) / len(earlier)
    if change <= -TREND_THRESHOLD:
        return "declining", change
    if change >= TREND_THRESHOLD:
        return "improving", change
    return "stable", change


class _ConceptAccumulator:
    def __init__(self) -> None:
        self.attempts = 0
        self.correct = 0
        self.recent: deque[int] = deque(maxlen=2 * TREND_HALF_WINDOW)
        self.last_interaction: dict[str, Any] | None = None

    def update(self, label: int | None, interaction: Mapping[str, Any]) -> None:
        self.last_interaction = dict(interaction)
        if label is not None:
            self.attempts += 1
            self.correct += label
            self.recent.append(label)

    def to_state(self, concept_id: str) -> dict[str, Any]:
        incorrect = self.attempts - self.correct
        historical = self.correct / self.attempts if self.attempts else None
        recent_values = list(self.recent)[-RECENT_CONCEPT_WINDOW:]
        recent = sum(recent_values) / len(recent_values) if recent_values else None
        smoothed = (
            (self.correct + BETA_PRIOR_ALPHA)
            / (self.attempts + BETA_PRIOR_ALPHA + BETA_PRIOR_BETA)
        )
        interval = wilson_interval(self.correct, self.attempts)
        evidence, confidence, uncertainty, reasons = _evidence_labels(self.attempts, interval)
        trend_name, trend_delta = _trend(self.recent)
        issues: list[str] = []
        if self.attempts < 5:
            issues.append("insufficient_evidence")
        if len(recent_values) >= 3 and sum(recent_values) <= len(recent_values) - 3:
            issues.append("repeated_recent_incorrect_responses")
        if trend_name == "declining":
            issues.append("recent_performance_decline")
        if len(recent_values) >= 4 and 2 <= sum(recent_values) <= len(recent_values) - 2:
            issues.append("inconsistent_recent_responses")
        return {
            "concept_id": concept_id,
            "attempts": self.attempts,
            "correct": self.correct,
            "incorrect": incorrect,
            "historical_accuracy": historical,
            "recent_accuracy": recent,
            "smoothed_performance": smoothed,
            "performance_trend": trend_name,
            "performance_change": trend_delta,
            "last_observed_interaction": self.last_interaction,
            "evidence_count": self.attempts,
            "evidence_sufficiency": evidence,
            "estimate_confidence": confidence,
            "uncertainty_level": uncertainty,
            "uncertainty_interval_95": interval,
            "uncertainty_reason": reasons,
            "potential_issues": issues,
            "evidence_type": "observed_correctness_and_derived_statistics",
        }


class LearnerStateAccumulator:
    """Incrementally build a learner's state from current-and-past rows only.

    A snapshot is always a state after the rows already passed to ``update``.
    Replaying a learner through a selected cutoff reconstructs its historical
    state without accessing any later event.
    """

    def __init__(self, learner_id: str) -> None:
        if not learner_id:
            raise ValueError("learner_id is required")
        self.learner_id = str(learner_id)
        self.total_interactions = 0
        self.labelled_responses = 0
        self.correct_responses = 0
        self.unlabelled_interactions = 0
        self.missing_skill_mapping_interactions = 0
        self.duplicate_interactions = 0
        self.concepts: dict[str, _ConceptAccumulator] = defaultdict(_ConceptAccumulator)
        self.overall_recent: deque[int] = deque(maxlen=2 * TREND_HALF_WINDOW)
        self.last_state_timestamp: str | None = None
        self._last_numeric_timestamp: int | None = None
        self._last_source_order: int | None = None
        self._last_question_id: str | None = None
        self._last_prediction: dict[str, Any] = {
            "next_response_correctness": None,
            "model_name": None,
            "availability": "unavailable",
            "reason": "No existing model artifact could be loaded in the documented project environment during this run.",
        }

    def update(self, row: Mapping[str, Any]) -> None:
        row_learner = str(row.get("learner_id", self.learner_id))
        if row_learner != self.learner_id:
            raise ValueError(f"row learner {row_learner!r} does not match state {self.learner_id!r}")
        source_order_raw = row.get("source_row_order")
        if source_order_raw not in (None, ""):
            source_order = int(source_order_raw)
            if self._last_source_order is not None and source_order <= self._last_source_order:
                raise ValueError("source_row_order must strictly increase")
            self._last_source_order = source_order
        timestamp, numeric_timestamp = _parse_timestamp(row.get("timestamp"))
        if (numeric_timestamp is not None and self._last_numeric_timestamp is not None
                and numeric_timestamp < self._last_numeric_timestamp):
            raise ValueError("timestamps must be nondecreasing in source order")
        if numeric_timestamp is not None:
            self._last_numeric_timestamp = numeric_timestamp
        if timestamp is not None:
            self.last_state_timestamp = timestamp

        label = _parse_label(row.get("correctness"))
        concepts = skill_ids(row.get("skill_tags", row.get("current_skill_tags", "")))
        source_order_value = row.get("source_row_order")
        interaction = {
            "question_id": str(row.get("question_id", row.get("current_question_id", ""))) or None,
            "source_row_order": int(source_order_value) if source_order_value not in (None, "") else None,
            "timestamp": timestamp,
        }
        self.total_interactions += 1
        self._last_question_id = interaction["question_id"]
        if label is None:
            self.unlabelled_interactions += 1
        else:
            self.labelled_responses += 1
            self.correct_responses += label
            self.overall_recent.append(label)
        if not concepts:
            self.missing_skill_mapping_interactions += 1
        for concept_id in concepts:
            self.concepts[concept_id].update(label, interaction)
        if str(row.get("is_exact_duplicate", "0")) == "1":
            self.duplicate_interactions += 1

    def set_next_response_prediction(self, probability: float, model_name: str) -> None:
        """Attach a supplied verified inference; never reinterpret it as cognition."""
        probability = float(probability)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError("prediction probability must be finite and within [0,1]")
        if not model_name:
            raise ValueError("model_name is required for a supplied prediction")
        self._last_prediction = {
            "next_response_correctness": probability,
            "model_name": str(model_name),
            "availability": "provided_by_caller",
            "reason": "Prediction supplied explicitly by a caller; it remains a response-outcome prediction, not an understanding estimate.",
            "interpretation": "predicted_probability_of_recorded_next_response_correctness_only",
            "calibration_status": "not_assessed_by_learner_state_module",
        }

    def snapshot(self) -> dict[str, Any]:
        attempts = self.labelled_responses
        correct = self.correct_responses
        historical = correct / attempts if attempts else None
        recent_values = list(self.overall_recent)[-RECENT_OVERALL_WINDOW:]
        recent = sum(recent_values) / len(recent_values) if recent_values else None
        smoothed = (
            (correct + BETA_PRIOR_ALPHA)
            / (attempts + BETA_PRIOR_ALPHA + BETA_PRIOR_BETA)
        )
        interval = wilson_interval(correct, attempts)
        evidence, confidence, uncertainty, reasons = _evidence_labels(attempts, interval)
        trend_name, trend_delta = _trend(self.overall_recent)
        potential_issues: list[str] = []
        if attempts < 5:
            potential_issues.append("insufficient_evidence")
        if len(recent_values) >= 3 and sum(recent_values) <= len(recent_values) - 3:
            potential_issues.append("repeated_recent_incorrect_responses")
        if trend_name == "declining":
            potential_issues.append("recent_performance_decline")
        if len(recent_values) >= 4 and 2 <= sum(recent_values) <= len(recent_values) - 2:
            potential_issues.append("inconsistent_recent_responses")
        state = {
            "schema_version": "1.0",
            "learner_id": self.learner_id,
            "state_timestamp": self.last_state_timestamp,
            "observation_window": {
                "type": "all_rows_seen_through_state_timestamp",
                "recent_overall_labeled_responses": RECENT_OVERALL_WINDOW,
                "recent_concept_labeled_responses": RECENT_CONCEPT_WINDOW,
                "trend_comparison": "latest_5_vs_preceding_5_labeled_responses",
            },
            "observation_summary": {
                "total_interactions": self.total_interactions,
                "labelled_responses": attempts,
                "unlabelled_interactions": self.unlabelled_interactions,
                "unique_concepts_observed": len(self.concepts),
                "interactions_without_skill_mapping": self.missing_skill_mapping_interactions,
                "preserved_duplicate_interactions": self.duplicate_interactions,
            },
            "learning_performance": {
                "estimated_performance": smoothed,
                "recent_performance": recent,
                "historical_performance": historical,
                "performance_change": trend_delta,
                "performance_trend": trend_name,
                "attempts": attempts,
                "correct": correct,
                "incorrect": attempts - correct,
                "evidence_type": "observed_correctness_and_derived_statistics",
                "evidence_sufficiency": evidence,
                "estimate_confidence": confidence,
                "uncertainty_level": uncertainty,
                "uncertainty_interval_95": interval,
                "uncertainty_reason": reasons,
                "potential_issues": potential_issues,
            },
            "concept_states": [
                self.concepts[concept_id].to_state(concept_id)
                for concept_id in sorted(self.concepts)
            ],
            "model_predictions": dict(self._last_prediction),
            "limitations": list(LIMITATIONS),
        }
        validate_state(state)
        return state


def build_state_from_rows(learner_id: str, rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    accumulator = LearnerStateAccumulator(learner_id)
    for row in rows:
        accumulator.update(row)
    return accumulator.snapshot()
