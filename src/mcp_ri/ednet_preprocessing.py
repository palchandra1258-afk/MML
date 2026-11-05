"""Leakage-aware, streaming feature construction for EdNet KT1."""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict, deque
from typing import Any, Iterable, Iterator, Mapping

from .ednet_validation import derive_correctness, is_missing, parse_timestamp


SOURCE_DATASET = "EdNet-KT1"
RAW_COLUMNS = ("timestamp", "solving_id", "question_id", "user_answer", "elapsed_time")
FEATURE_COLUMNS = (
    "current_question_id",
    "current_part",
    "current_skill_tags",
    "n_prior_logged_events",
    "n_prior_answered_attempts",
    "n_prior_correct",
    "prior_accuracy",
    "recent_5_accuracy",
    "recent_10_accuracy",
    "recent_accuracy_trend_5",
    "previous_response_correctness",
    "previous_response_skill_tags",
    "previous_elapsed_time_ms",
    "gap_since_previous_question_ms",
    "prior_skill_tag_attempts",
    "prior_skill_tag_correct",
    "prior_skill_tag_accuracy",
)
SPLIT_NAMES = ("train", "validation", "test")
QUESTION_ID_RE = re.compile(r"^q[0-9]+$")
ANSWER_RE = re.compile(r"^[a-d]$")


def parse_skill_tags(value: Any) -> tuple[str, ...]:
    if is_missing(value):
        return ()
    raw = str(value).strip()
    if raw == "-1":
        return ()
    tags = tuple(tag.strip() for tag in raw.split(";") if tag.strip())
    return tuple(tag for tag in tags if tag != "-1")


def parse_nonnegative_int(value: Any) -> int | None:
    if is_missing(value):
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def split_unseen_learner(learner_id: str, seed: int = 2025) -> str:
    """Stable 70/15/15 assignment, independent of Python's randomized hash."""
    digest = hashlib.blake2b(
        f"{seed}:{learner_id}".encode("utf-8"), digest_size=8, person=b"mcpri-v1"
    ).digest()
    bucket = int.from_bytes(digest, "big") % 10_000
    if bucket < 7_000:
        return "train"
    if bucket < 8_500:
        return "validation"
    return "test"


def temporal_split_bounds(eligible_count: int) -> tuple[int, int]:
    """Return target-index boundaries; guarantee the first target is training."""
    if eligible_count <= 0:
        return 0, 0
    train_end = min(eligible_count, max(1, int(eligible_count * 0.70)))
    validation_end = min(eligible_count, max(train_end, int(eligible_count * 0.85)))
    return train_end, validation_end


def temporal_split_for_position(position: int, eligible_count: int) -> str:
    train_end, validation_end = temporal_split_bounds(eligible_count)
    if position < train_end:
        return "train"
    if position < validation_end:
        return "validation"
    return "test"


def _normalize_raw_row(raw: Mapping[str, Any]) -> dict[str, str]:
    return {name: "" if raw.get(name) is None else str(raw.get(name)).strip() for name in RAW_COLUMNS}


def process_learner_rows(
    learner_id: str,
    raw_rows: Iterable[Mapping[str, Any]],
    question_content: Mapping[str, Mapping[str, str]],
    *,
    seed: int = 2025,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Build one learner's rows in source order; memory is bounded to one learner."""
    rows = [_normalize_raw_row(row) for row in raw_rows]
    normalized: list[dict[str, Any]] = []
    eligible_count = 0
    stats: Counter[str] = Counter()
    seen_records: set[tuple[str, ...]] = set()
    previous_timestamp: int | None = None

    for source_order, raw in enumerate(rows):
        timestamp = parse_timestamp(raw["timestamp"])
        if timestamp is None:
            stats["invalid_timestamps"] += 1
        elif previous_timestamp is not None and timestamp < previous_timestamp:
            raise ValueError(
                f"timestamps decrease for learner {learner_id} at source row {source_order}; "
                "the processor will not reorder events"
            )
        if timestamp is not None:
            previous_timestamp = timestamp
        qid = raw["question_id"]
        if not QUESTION_ID_RE.fullmatch(qid):
            stats["invalid_question_ids"] += 1
        content = question_content.get(qid)
        if content is None:
            stats["unmatched_question_ids"] += 1
            content = {}
        answer = raw["user_answer"].lower()
        correct_answer = str(content.get("correct_answer", "")).strip().lower()
        derived_correctness = derive_correctness(answer, correct_answer)
        correctness = int(derived_correctness) if derived_correctness is not None else None
        if is_missing(answer):
            stats["blank_answers"] += 1
        elif not ANSWER_RE.fullmatch(answer):
            stats["invalid_answers"] += 1
        elif correctness is None:
            stats["unlabelled_nonblank_answers"] += 1
        else:
            eligible_count += 1
            stats["eligible_targets"] += 1

        key = tuple(raw[column] for column in RAW_COLUMNS)
        duplicate = key in seen_records
        if duplicate:
            stats["exact_duplicate_rows"] += 1
        else:
            seen_records.add(key)
        stats["interaction_rows"] += 1
        for name, value in raw.items():
            if is_missing(value):
                stats[f"blank_{name}"] += 1
        if parse_nonnegative_int(raw["elapsed_time"]) is None:
            stats["unavailable_elapsed_time"] += 1

        tags = parse_skill_tags(content.get("tags", ""))
        if not tags:
            stats["missing_skill_tag_rows"] += 1
        normalized.append(
            {
                "raw": raw,
                "timestamp_int": timestamp,
                "content": content,
                "tags": tags,
                "correctness": correctness,
                "is_exact_duplicate": duplicate,
                "source_row_order": source_order,
            }
        )

    unseen_split = split_unseen_learner(learner_id, seed)
    result: list[dict[str, Any]] = []
    prior_outcomes: deque[int] = deque(maxlen=10)
    prior_skill: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    n_prior_correct = 0
    n_prior_answered = 0
    previous_labeled: dict[str, Any] | None = None
    previous_event: dict[str, Any] | None = None
    previous_event_timestamp: int | None = None
    eligible_position = 0

    for event in normalized:
        raw = event["raw"]
        content = event["content"]
        tags: tuple[str, ...] = event["tags"]
        timestamp = event["timestamp_int"]
        label = event["correctness"]

        recent = list(prior_outcomes)
        recent5 = recent[-5:]
        trend = (sum(recent5) / len(recent5) - sum(recent[-10:-5]) / 5) if len(recent) >= 10 else None
        matched_tag_counts = [prior_skill[tag] for tag in tags if tag in prior_skill]
        skill_attempts = sum(item[0] for item in matched_tag_counts) if tags else None
        skill_correct = sum(item[1] for item in matched_tag_counts) if tags else None
        skill_accuracy = skill_correct / skill_attempts if skill_attempts else (0.0 if tags else None)
        gap = (
            timestamp - previous_event_timestamp
            if timestamp is not None and previous_event_timestamp is not None
            else None
        )
        elapsed_previous = parse_nonnegative_int(previous_event["raw"]["elapsed_time"]) if previous_event else None

        row = {
            "learner_id": learner_id,
            "source_row_order": event["source_row_order"],
            "timestamp": raw["timestamp"],
            "question_id": raw["question_id"],
            "submitted_answer": raw["user_answer"],
            "correct_answer": content.get("correct_answer", ""),
            "correctness": label,
            "skill_tags": ";".join(tags),
            "session_id": raw["solving_id"],
            "source_dataset": SOURCE_DATASET,
            "elapsed_time_ms": raw["elapsed_time"],
            "is_exact_duplicate": int(event["is_exact_duplicate"]),
            "split_unseen_learner": unseen_split if label is not None else "",
            "split_future_known_learner": (
                temporal_split_for_position(eligible_position, eligible_count) if label is not None else ""
            ),
            "current_question_id": raw["question_id"],
            "current_part": content.get("part", ""),
            "current_skill_tags": ";".join(tags),
            "n_prior_logged_events": event["source_row_order"],
            "n_prior_answered_attempts": n_prior_answered,
            "n_prior_correct": n_prior_correct,
            "prior_accuracy": n_prior_correct / n_prior_answered if n_prior_answered else None,
            "recent_5_accuracy": sum(recent5) / len(recent5) if recent5 else None,
            "recent_10_accuracy": sum(recent) / len(recent) if recent else None,
            "recent_accuracy_trend_5": trend,
            "previous_response_correctness": previous_labeled["correctness"] if previous_labeled else None,
            "previous_response_skill_tags": ";".join(previous_labeled["tags"]) if previous_labeled else "",
            "previous_elapsed_time_ms": elapsed_previous,
            "gap_since_previous_question_ms": gap,
            "prior_skill_tag_attempts": skill_attempts,
            "prior_skill_tag_correct": skill_correct,
            "prior_skill_tag_accuracy": skill_accuracy,
        }
        result.append(row)

        if label is not None:
            eligible_position += 1
            prior_outcomes.append(int(label))
            n_prior_answered += 1
            n_prior_correct += int(label)
            for tag in tags:
                prior_skill[tag][0] += 1
                prior_skill[tag][1] += int(label)
            previous_labeled = {"correctness": int(label), "tags": tags}
        previous_event_timestamp = timestamp if timestamp is not None else previous_event_timestamp
        previous_event = event

    stats["learners"] = 1
    stats[f"unseen_{unseen_split}_targets"] = eligible_count
    return result, dict(stats)


def output_columns() -> tuple[str, ...]:
    metadata = (
        "learner_id", "source_row_order", "timestamp", "question_id", "submitted_answer",
        "correct_answer", "correctness", "skill_tags", "session_id", "source_dataset", "elapsed_time_ms",
        "is_exact_duplicate", "split_unseen_learner", "split_future_known_learner",
    )
    return metadata + FEATURE_COLUMNS


def assert_no_target_leakage(columns: Iterable[str] = FEATURE_COLUMNS) -> None:
    forbidden = {"submitted_answer", "correct_answer", "correctness", "elapsed_time", "elapsed_time_ms"}
    overlap = forbidden.intersection(columns)
    if overlap:
        raise ValueError(f"target/post-response fields found in model feature list: {sorted(overlap)}")

