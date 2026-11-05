"""Streaming integrity/schema/data-quality checks for official EdNet KT1 ZIPs."""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


KT1_REQUIRED_COLUMNS = {"timestamp", "solving_id", "question_id", "user_answer", "elapsed_time"}
QUESTION_REQUIRED_COLUMNS = {"question_id", "correct_answer", "tags"}
LEARNER_FILE_RE = re.compile(r"^u?[0-9]+$")
QUESTION_ID_RE = re.compile(r"^q[0-9]+$")
ANSWER_RE = re.compile(r"^[a-d]$")


def is_missing(value: Any) -> bool:
    """Treat empty/whitespace cells as missing; preserve sentinels such as -1."""
    return value is None or str(value).strip() == ""


def parse_timestamp(value: Any) -> int | None:
    if is_missing(value):
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def learner_id_from_member(member_name: str) -> str | None:
    basename = PurePosixPath(member_name).name
    if not basename.lower().endswith(".csv"):
        return None
    candidate = basename[:-4]
    return candidate if LEARNER_FILE_RE.fullmatch(candidate) else None


def validate_schema(columns: Iterable[str], required: set[str] = KT1_REQUIRED_COLUMNS) -> list[str]:
    present = {str(name).strip() for name in columns}
    return sorted(required - present)


def derive_correctness(user_answer: Any, correct_answer: Any) -> bool | None:
    if is_missing(user_answer) or is_missing(correct_answer):
        return None
    answer = str(user_answer).strip().lower()
    key = str(correct_answer).strip().lower()
    if not ANSWER_RE.fullmatch(answer) or not ANSWER_RE.fullmatch(key):
        return None
    return answer == key


def _read_csv_rows(archive: zipfile.ZipFile, member: str):
    return csv.DictReader(io.TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline=""))


def find_question_member(archive: zipfile.ZipFile) -> str:
    candidates = [
        info.filename
        for info in archive.infolist()
        if PurePosixPath(info.filename).name.lower() in {"questions.csv", "question.csv"}
    ]
    if not candidates:
        raise ValueError("question-content ZIP has no questions.csv or question.csv member")
    return candidates[0]


def load_question_content(archive_path: Path) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    with zipfile.ZipFile(archive_path) as archive:
        member = find_question_member(archive)
        rows = _read_csv_rows(archive, member)
        columns = rows.fieldnames or []
        missing_columns = validate_schema(columns, QUESTION_REQUIRED_COLUMNS)
        if missing_columns:
            raise ValueError(f"question-content schema missing columns: {missing_columns}")
        content: dict[str, dict[str, str]] = {}
        duplicate_ids = 0
        total_rows = 0
        missing_answer = 0
        missing_tags = 0
        invalid_ids = 0
        for row in rows:
            total_rows += 1
            qid = (row.get("question_id") or "").strip()
            if not QUESTION_ID_RE.fullmatch(qid):
                invalid_ids += 1
            if is_missing(row.get("correct_answer")):
                missing_answer += 1
            if is_missing(row.get("tags")) or (row.get("tags") or "").strip() == "-1":
                missing_tags += 1
            if qid in content:
                duplicate_ids += 1
                continue
            content[qid] = {key: (value or "").strip() for key, value in row.items() if key}
        metadata = {
            "member": member,
            "columns": columns,
            "rows": total_rows,
            "unique_question_ids": len(content),
            "duplicate_question_id_rows": duplicate_ids,
            "invalid_question_id_rows": invalid_ids,
            "missing_answer_key_rows": missing_answer,
            "missing_or_sentinel_tag_rows": missing_tags,
        }
        return content, metadata


def inspect_archives(kt1_path: Path, content_path: Path) -> dict[str, Any]:
    questions, content_summary = load_question_content(content_path)
    summary: dict[str, Any] = {
        "kt1_archive": str(kt1_path),
        "question_content_archive": str(content_path),
        "learner_files": 0,
        "interaction_rows": 0,
        "columns": [],
        "missing_values_by_column": {},
        "duplicate_records": 0,
        "valid_timestamps": 0,
        "invalid_timestamps": 0,
        "non_monotonic_timestamp_transitions": 0,
        "duplicate_timestamp_transitions": 0,
        "question_id_rows": 0,
        "invalid_question_id_rows": 0,
        "unmatched_question_rows": 0,
        "unmatched_unique_question_ids": 0,
        "matched_question_rows": 0,
        "answer_key_available_rows": 0,
        "answer_key_missing_or_invalid_rows": 0,
        "correctness_derivable_rows": 0,
        "skill_tag_available_rows": 0,
        "skill_tag_missing_rows": 0,
        "invalid_answer_rows": 0,
        "per_learner_rows_min": None,
        "per_learner_rows_max": 0,
        "_columns": set(),
        "_missing": Counter(),
        "_unmatched_qids": set(),
    }

    with zipfile.ZipFile(kt1_path) as archive:
        learner_members = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir() and learner_id_from_member(info.filename) is not None
        ]
        seen_learner_ids: set[str] = set()
        started = time.monotonic()
        for member in learner_members:
            learner_id = learner_id_from_member(member)
            if learner_id is None:
                continue
            if learner_id in seen_learner_ids:
                raise ValueError(f"duplicate learner ID represented by multiple files: {learner_id}")
            seen_learner_ids.add(learner_id)
            summary["learner_files"] += 1
            reader = _read_csv_rows(archive, member)
            columns = reader.fieldnames or []
            summary["_columns"].update(columns)
            missing_columns = validate_schema(columns)
            if missing_columns:
                raise ValueError(f"KT1 schema missing columns in {member}: {missing_columns}")
            row_count = 0
            prior_timestamp: int | None = None
            prior_rows: set[tuple[tuple[str, str], ...]] = set()
            for row in reader:
                row_count += 1
                summary["interaction_rows"] += 1
                for column in columns:
                    value = row.get(column)
                    if is_missing(value):
                        summary["_missing"][column] += 1

                exact_record = tuple(sorted((key, value or "") for key, value in row.items() if key))
                if exact_record in prior_rows:
                    summary["duplicate_records"] += 1
                else:
                    prior_rows.add(exact_record)

                timestamp = parse_timestamp(row.get("timestamp"))
                if timestamp is None:
                    summary["invalid_timestamps"] += 1
                else:
                    summary["valid_timestamps"] += 1
                    if prior_timestamp is not None:
                        if timestamp < prior_timestamp:
                            summary["non_monotonic_timestamp_transitions"] += 1
                        elif timestamp == prior_timestamp:
                            summary["duplicate_timestamp_transitions"] += 1
                    prior_timestamp = timestamp

                qid = (row.get("question_id") or "").strip()
                summary["question_id_rows"] += 1
                if not QUESTION_ID_RE.fullmatch(qid):
                    summary["invalid_question_id_rows"] += 1
                    continue
                question = questions.get(qid)
                if question is None:
                    summary["unmatched_question_rows"] += 1
                    summary["_unmatched_qids"].add(qid)
                    continue
                summary["matched_question_rows"] += 1
                key = question.get("correct_answer", "")
                if not is_missing(key) and ANSWER_RE.fullmatch(key.lower()):
                    summary["answer_key_available_rows"] += 1
                    if derive_correctness(row.get("user_answer"), key) is not None:
                        summary["correctness_derivable_rows"] += 1
                else:
                    summary["answer_key_missing_or_invalid_rows"] += 1
                tags = question.get("tags", "")
                if not is_missing(tags) and tags != "-1":
                    summary["skill_tag_available_rows"] += 1
                else:
                    summary["skill_tag_missing_rows"] += 1
                answer = (row.get("user_answer") or "").strip().lower()
                if answer and not ANSWER_RE.fullmatch(answer):
                    summary["invalid_answer_rows"] += 1

            summary["per_learner_rows_min"] = (
                row_count if summary["per_learner_rows_min"] is None
                else min(summary["per_learner_rows_min"], row_count)
            )
            summary["per_learner_rows_max"] = max(summary["per_learner_rows_max"], row_count)
            if summary["learner_files"] % 10000 == 0:
                elapsed = time.monotonic() - started
                print(
                    f"Scanned {summary['learner_files']:,}/{len(learner_members):,} learner files "
                    f"({elapsed:.0f}s)",
                    file=sys.stderr,
                    flush=True,
                )

    summary["columns"] = sorted(summary.pop("_columns"))
    summary["missing_values_by_column"] = dict(sorted(summary.pop("_missing").items()))
    summary["unmatched_unique_question_ids"] = len(summary.pop("_unmatched_qids"))
    summary["question_content"] = content_summary
    if summary["interaction_rows"]:
        summary["question_content_coverage"] = summary["matched_question_rows"] / summary["interaction_rows"]
        summary["answer_key_coverage"] = summary["correctness_derivable_rows"] / summary["interaction_rows"]
        summary["skill_tag_coverage"] = summary["skill_tag_available_rows"] / summary["interaction_rows"]
    else:
        summary["question_content_coverage"] = None
        summary["answer_key_coverage"] = None
        summary["skill_tag_coverage"] = None
    summary["prediction_task_supported"] = bool(
        summary["interaction_rows"] > 0
        and summary["learner_files"] > 0
        and summary["correctness_derivable_rows"] > 0
        and "timestamp" in summary["columns"]
    )
    summary["input_target_policy"] = {
        "input_cutoff": "strictly before the current target response is submitted",
        "target": "user_answer == joined question-content correct_answer",
        "prohibited_current_response_inputs": ["user_answer", "derived correctness", "elapsed_time"],
        "future_interactions": "must not be used to construct prior-history features",
        "question_metadata": "question_id, bundle_id, part and expert tags may be used only if available before response",
    }
    return summary


def write_reports(
    summary: dict[str, Any], report_dir: Path, docs_dir: Path
) -> tuple[Path, Path, Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "ednet_quality_summary.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    md_path = docs_dir / "EDNET_DATA_QUALITY_REPORT.md"
    md = [
        "# EdNet KT1 Data Quality Report",
        "",
        "Generated from the acquired official archives. This report contains aggregate counts only; it does not publish learner IDs or response records.",
        "",
        "## Dataset counts",
        "",
        f"- Learner files: {summary['learner_files']:,}",
        f"- Interaction rows: {summary['interaction_rows']:,}",
        f"- Question-content rows: {summary['question_content']['rows']:,}",
        f"- Unique question IDs in content: {summary['question_content']['unique_question_ids']:,}",
        "",
        "## Schema and missing values",
        "",
        f"- KT1 columns: {', '.join(summary['columns'])}",
        f"- Missing values by column: `{json.dumps(summary['missing_values_by_column'], sort_keys=True)}`",
        f"- Duplicate complete records within learner files: {summary['duplicate_records']:,}",
        "",
        "## Timestamp and mapping checks",
        "",
        f"- Valid timestamps: {summary['valid_timestamps']:,}",
        f"- Invalid/missing timestamps: {summary['invalid_timestamps']:,}",
        f"- Non-monotonic adjacent transitions: {summary['non_monotonic_timestamp_transitions']:,}",
        f"- Equal adjacent timestamp transitions: {summary['duplicate_timestamp_transitions']:,}",
        f"- Matched response rows: {summary['matched_question_rows']:,}",
        f"- Unmatched response rows: {summary['unmatched_question_rows']:,} ({summary['unmatched_unique_question_ids']:,} unique question IDs)",
        f"- Rows with usable answer key and submitted answer: {summary['correctness_derivable_rows']:,}",
        f"- Rows with skill tags: {summary['skill_tag_available_rows']:,}",
        f"- Invalid submitted-answer rows: {summary['invalid_answer_rows']:,}",
        "",
        "## Prediction-task feasibility",
        "",
        f"- Structural feasibility: **{'yes' if summary['prediction_task_supported'] else 'no'}**",
        "- Target: submitted answer matches the joined official answer key. This is a behavioral response-outcome target, not a direct measure of understanding, confusion or cognitive state.",
        "- Current answer, derived target and current elapsed time are excluded from inputs; historical features must use strictly earlier interactions.",
        "",
        "See `ednet_quality_summary.json` for complete aggregate fields.",
        "",
    ]
    md_path.write_text("\n".join(md))
    schema_path = docs_dir / "EDNET_SCHEMA.md"
    schema = [
        "# EdNet KT1 Schema Observed During Validation",
        "",
        "This file is generated from the actual archive headers. Values below are descriptive schema/coverage facts, not assumptions from the README.",
        "",
        f"- KT1 columns: {', '.join(summary['columns'])}",
        f"- Question-content columns: {', '.join(summary['question_content']['columns'])}",
        f"- Learner files: {summary['learner_files']:,}",
        f"- Interactions: {summary['interaction_rows']:,}",
        "",
        "## Target and leakage boundary",
        "",
        "Target correctness is derived by joining KT1 `question_id` to question content `correct_answer` and comparing with current `user_answer`. The current target row's submitted answer and `elapsed_time` are not input features. For each prediction row, history may contain only responses with earlier ordering for that learner. Metadata about the current question is permitted only if it is available before submission.",
        "",
    ]
    schema_path.write_text("\n".join(schema))
    dataset_path = docs_dir / "EDNET_DATASET_REPORT.md"
    dataset = [
        "# EdNet KT1 Dataset Report",
        "",
        "## Source, license and scope",
        "",
        "Source: [official Riiid EdNet repository](https://github.com/riiid/ednet). The repository specifies EdNet KT1 as learner-separated question-response logs and publishes the question-content table. The repository license is CC BY-NC 4.0: use is non-commercial, attribution is required, and these files must not be republished without confirming permission. The experiment predicts a behavioral response outcome; it is not a direct measurement of understanding, confusion or cognitive state.",
        "",
        "## Observed acquisition and dataset size",
        "",
        f"- KT1 archive bytes: {summary['acquisition']['kt1_size_bytes']:,}",
        f"- KT1 SHA-256: `{summary['acquisition']['kt1_sha256']}`",
        f"- Question-content archive bytes: {summary['acquisition']['content_size_bytes']:,}",
        f"- Question-content SHA-256: `{summary['acquisition']['content_sha256']}`",
        f"- Learner CSV files: {summary['learner_files']:,}",
        f"- KT1 interaction rows: {summary['interaction_rows']:,}",
        f"- Unique questions in content table: {summary['question_content']['unique_question_ids']:,}",
        "",
        "## Dataset structure and task suitability",
        "",
        f"- Observed KT1 columns: {', '.join(summary['columns'])}",
        f"- Observed question-content columns: {', '.join(summary['question_content']['columns'])}",
        f"- Rows with a derivable correctness target: {summary['correctness_derivable_rows']:,}",
        f"- Correctness-target coverage across KT1 rows: {summary['answer_key_coverage']:.6f}" if summary["answer_key_coverage"] is not None else "- Correctness-target coverage: unavailable",
        f"- Structural support for the proposed task: **{'yes' if summary['prediction_task_supported'] else 'no'}**",
        "",
        "Target correctness is obtained by joining the current response's `question_id` to the content table's `correct_answer`, then comparing it with current `user_answer`. For a prediction example, the current submitted answer, derived correctness and current `elapsed_time` are target/post-response information and are prohibited from input features. Current-question metadata is permitted only if it is available before the answer is submitted. Historical input may use strictly earlier learner interactions only.",
        "",
        "## Integrity and limits",
        "",
        "Both archives passed ZIP structure and per-member CRC checks during acquisition. SHA-256 values above identify the preserved raw files. Timestamps are shifted in the published dataset; sequence ordering is validated within each learner file, and absolute calendar time should not be interpreted as original time. See the separate data-quality report for missingness, duplicate, chronology and mapping findings.",
        "",
    ]
    dataset_path.write_text("\n".join(dataset))
    return dataset_path, schema_path, md_path, json_path
