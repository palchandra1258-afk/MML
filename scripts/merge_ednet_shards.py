#!/usr/bin/env python3
"""Merge ordered gzip CSV shards and aggregate their preprocessing summaries."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


ADDITIVE_COUNTS = (
    "learners_processed", "interactions_written", "eligible_supervised_targets",
    "blank_answers_excluded_as_targets", "invalid_answers_excluded_as_targets",
    "unlabelled_nonblank_answers", "exact_duplicate_rows_preserved",
    "unmatched_question_ids", "invalid_question_ids", "invalid_timestamps",
    "unavailable_elapsed_time", "missing_skill_tag_rows",
)


def merge(shard_summaries: list[Path], output: Path, summary_output: Path) -> dict:
    if not shard_summaries:
        raise ValueError("provide at least one shard summary")
    summaries = [json.loads(path.read_text()) for path in shard_summaries]
    for left, right in zip(summaries, summaries[1:]):
        if left["seed"] != right["seed"]:
            raise ValueError("cannot merge shards with different seeds")
        if left["source_archives"] != right["source_archives"]:
            raise ValueError("cannot merge shards built from different raw archives")
        if left["model_feature_columns"] != right["model_feature_columns"] or left["output_columns"] != right["output_columns"]:
            raise ValueError("cannot merge shards with different schemas")
        if left["learner_index_end_exclusive"] != right["learner_index_start"]:
            raise ValueError("learner shard ranges must be contiguous and ordered")

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".part")
    with partial.open("wb") as destination:
        for summary in summaries:
            shard_path = Path(summary["output"]["path"])
            with shard_path.open("rb") as source:
                shutil.copyfileobj(source, destination, length=8 * 1024 * 1024)
    partial.replace(output)

    combined = dict(summaries[0])
    combined["output"] = {
        "path": str(output),
        "size_bytes": output.stat().st_size,
        "format": "ordered concatenated gzip members containing one gzip-compressed CSV stream; first shard carries the single header",
    }
    combined["learner_limit"] = None
    combined["learner_index_start"] = summaries[0]["learner_index_start"]
    combined["learner_index_end_exclusive"] = summaries[-1]["learner_index_end_exclusive"]
    for key in ADDITIVE_COUNTS:
        combined[key] = sum(item[key] for item in summaries)
    blank_fields: dict[str, int] = {}
    for item in summaries:
        for key, value in item["blank_raw_fields"].items():
            if key not in {"timestamp", "solving_id", "question_id", "user_answer", "elapsed_time"}:
                continue
            blank_fields[key] = blank_fields.get(key, 0) + value
    combined["blank_raw_fields"] = blank_fields
    combined["split_protocols"] = {}
    for protocol in ("unseen_learner", "future_known_learner"):
        combined["split_protocols"][protocol] = {}
        for split in ("train", "validation", "test"):
            combined["split_protocols"][protocol][split] = {
                key: sum(item["split_protocols"][protocol][split][key] for item in summaries)
                for key in ("learners", "targets", "correct_targets", "incorrect_targets")
            }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(combined, indent=2) + "\n")
    return combined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-summaries", nargs="+", type=Path, required=True, help="ordered per-shard JSON summaries")
    parser.add_argument("--output", type=Path, required=True, help="final .csv.gz path")
    parser.add_argument("--summary-output", type=Path, required=True, help="final preprocessing summary JSON path")
    args = parser.parse_args(argv)
    try:
        result = merge(args.shard_summaries, args.output, args.summary_output)
    except Exception as exc:
        print(f"Shard merge failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"Merged {result['learners_processed']:,} learners and {result['interactions_written']:,} interactions.")
    print(f"Eligible targets: {result['eligible_supervised_targets']:,}; output: {result['output']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
