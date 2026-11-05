#!/usr/bin/env python3
"""Stream EdNet KT1 into one compressed, leakage-aware supervised table."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.ednet_preprocessing import (  # noqa: E402
    FEATURE_COLUMNS,
    assert_no_target_leakage,
    output_columns,
    process_learner_rows,
)
from mcp_ri.ednet_validation import (  # noqa: E402
    find_question_member,
    learner_id_from_member,
    validate_schema,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_content(path: Path):
    with zipfile.ZipFile(path) as archive:
        member = find_question_member(archive)
        with archive.open(member) as source:
            text = io.TextIOWrapper(source, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            missing = validate_schema(reader.fieldnames or [], {"question_id", "correct_answer", "tags", "part"})
            if missing:
                raise ValueError(f"Question table is missing required fields: {missing}")
            content = {
                (row.get("question_id") or "").strip(): {
                    key: (value or "").strip() for key, value in row.items() if key
                }
                for row in reader
            }
        return content, member


def csv_cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root", type=Path,
        default=Path(os.environ.get("MCP_RI_DATA_DIR", ROOT / "data")),
        help="dataset root (default: MCP_RI_DATA_DIR or repository data/)",
    )
    parser.add_argument("--seed", type=int, default=2025, help="stable learner split seed (default: 2025)")
    parser.add_argument("--max-learners", type=int, help="development limit; omit to process all learners")
    parser.add_argument("--start-index", type=int, default=0, help="inclusive learner-member index for deterministic sharding")
    parser.add_argument("--end-index", type=int, help="exclusive learner-member index for deterministic sharding")
    parser.add_argument("--output", type=Path, help="output .csv.gz path (default: processed/ednet/ednet_kt1_features.csv.gz)")
    parser.add_argument("--summary-output", type=Path, help="JSON summary path (default: processed/ednet/ednet_preprocessing_summary.json)")
    parser.add_argument("--no-header", action="store_true", help="omit CSV header when producing a later concatenated gzip shard")
    parser.add_argument("--overwrite", action="store_true", help="replace the processed output after a successful run")
    args = parser.parse_args(argv)
    if args.max_learners is not None and args.max_learners <= 0:
        parser.error("--max-learners must be positive")
    if args.start_index < 0 or (args.end_index is not None and args.end_index < args.start_index):
        parser.error("learner index range must satisfy 0 <= start-index <= end-index")
    if args.max_learners is not None and (args.start_index != 0 or args.end_index is not None):
        parser.error("--max-learners cannot be combined with explicit learner index bounds")

    data_root = args.data_root.expanduser()
    raw_dir = data_root / "raw" / "ednet"
    kt1_path = raw_dir / "ednet-kt1.zip"
    content_path = raw_dir / "ednet-content.zip"
    output_path = args.output.expanduser() if args.output else data_root / "processed" / "ednet" / "ednet_kt1_features.csv.gz"
    summary_path = args.summary_output.expanduser() if args.summary_output else data_root / "processed" / "ednet" / "ednet_preprocessing_summary.json"
    partial_path = output_path.with_name(output_path.name + ".part")
    if not kt1_path.is_file() or not content_path.is_file():
        print("Both official raw EdNet archives are required under data/raw/ednet.", file=sys.stderr)
        return 2
    if output_path.exists() and not args.overwrite:
        print(f"Output already exists: {output_path}; choose another --output or use --overwrite.", file=sys.stderr)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    assert_no_target_leakage()
    try:
        content, content_member = load_content(content_path)
        with zipfile.ZipFile(kt1_path) as archive:
            members = [
                info.filename for info in archive.infolist()
                if not info.is_dir() and learner_id_from_member(info.filename) is not None
            ]
            if args.max_learners is not None:
                members = members[: args.max_learners]
            members = members[args.start_index:args.end_index]
            selected_start = args.start_index
            selected_end = selected_start + len(members)
            totals: Counter[str] = Counter()
            target_counts = {
                protocol: {split: Counter() for split in ("train", "validation", "test")}
                for protocol in ("unseen_learner", "future_known_learner")
            }
            learner_sets = {
                protocol: {split: set() for split in ("train", "validation", "test")}
                for protocol in ("unseen_learner", "future_known_learner")
            }
            columns = output_columns()
            started = time.monotonic()
            with partial_path.open("wb") as binary:
                with gzip.GzipFile(fileobj=binary, mode="wb", compresslevel=1, mtime=0, filename="") as gz:
                    with io.TextIOWrapper(gz, encoding="utf-8", newline="") as text:
                        writer = csv.writer(text, lineterminator="\n")
                        if not args.no_header:
                            writer.writerow(columns)
                        for member_index, member in enumerate(members, start=1):
                            learner_id = learner_id_from_member(member)
                            assert learner_id is not None
                            with io.TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline="") as source_text:
                                reader = csv.DictReader(source_text)
                                missing = validate_schema(reader.fieldnames or [], {
                                    "timestamp", "solving_id", "question_id", "user_answer", "elapsed_time"
                                })
                                if missing:
                                    raise ValueError(f"KT1 file {member} is missing columns: {missing}")
                                raw_rows = list(reader)
                            processed, local_counts = process_learner_rows(
                                learner_id, raw_rows, content, seed=args.seed
                            )
                            totals.update(local_counts)
                            for row in processed:
                                writer.writerow([csv_cell(row.get(column)) for column in columns])
                                if row["correctness"] is None:
                                    continue
                                for protocol, split_key in (
                                    ("unseen_learner", "split_unseen_learner"),
                                    ("future_known_learner", "split_future_known_learner"),
                                ):
                                    split = row[split_key]
                                    target_counts[protocol][split][str(row["correctness"])] += 1
                                    learner_sets[protocol][split].add(learner_id)
                            if member_index % 50000 == 0:
                                elapsed = time.monotonic() - started
                                print(
                                    f"Processed {member_index:,}/{len(members):,} learners "
                                    f"and {totals['interaction_rows']:,} interactions ({elapsed:.0f}s)",
                                    file=sys.stderr,
                                    flush=True,
                                )

        partial_path.replace(output_path)
        protocols = {}
        for protocol in target_counts:
            protocols[protocol] = {
                split: {
                    "learners": len(learner_sets[protocol][split]),
                    "targets": sum(target_counts[protocol][split].values()),
                    "correct_targets": target_counts[protocol][split]["1"],
                    "incorrect_targets": target_counts[protocol][split]["0"],
                }
                for split in ("train", "validation", "test")
            }
        summary = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_dataset": "EdNet-KT1",
            "source_archives": {
                "kt1": {"path": str(kt1_path), "size_bytes": kt1_path.stat().st_size, "sha256": sha256_file(kt1_path)},
                "question_content": {"path": str(content_path), "size_bytes": content_path.stat().st_size, "sha256": sha256_file(content_path), "member": content_member},
            },
            "output": {"path": str(output_path), "size_bytes": output_path.stat().st_size, "format": "gzip-compressed CSV; one row per raw KT1 interaction"},
            "seed": args.seed,
            "learner_limit": args.max_learners,
            "learner_index_start": selected_start,
            "learner_index_end_exclusive": selected_end,
            "learners_processed": totals["learners"],
            "interactions_written": totals["interaction_rows"],
            "eligible_supervised_targets": totals["eligible_targets"],
            "blank_answers_excluded_as_targets": totals["blank_answers"],
            "invalid_answers_excluded_as_targets": totals["invalid_answers"],
            "unlabelled_nonblank_answers": totals["unlabelled_nonblank_answers"],
            "exact_duplicate_rows_preserved": totals["exact_duplicate_rows"],
            "unmatched_question_ids": totals["unmatched_question_ids"],
            "invalid_question_ids": totals["invalid_question_ids"],
            "invalid_timestamps": totals["invalid_timestamps"],
            "unavailable_elapsed_time": totals["unavailable_elapsed_time"],
            "missing_skill_tag_rows": totals["missing_skill_tag_rows"],
            "blank_raw_fields": {
                key[6:]: value for key, value in totals.items()
                if key.startswith("blank_") and key[6:] in {"timestamp", "solving_id", "question_id", "user_answer", "elapsed_time"}
            },
            "split_protocols": protocols,
            "model_feature_columns": list(FEATURE_COLUMNS),
            "output_columns": list(columns),
            "target_leakage_guard": "Current submitted_answer, correct_answer, correctness and current elapsed_time_ms are not in model_feature_columns.",
        }
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    except Exception as exc:
        print(f"Preprocessing failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Processed {totals['learners']:,} learners and {totals['interaction_rows']:,} interactions.")
    print(f"Eligible supervised targets: {totals['eligible_targets']:,}; blank answers retained without targets: {totals['blank_answers']:,}.")
    print(f"Processed data: {output_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
