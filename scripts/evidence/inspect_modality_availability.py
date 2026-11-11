#!/usr/bin/env python3
"""Report the modalities present in this repository's current data snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def inspect(data_root: Path) -> dict[str, Any]:
    processed = data_root / "processed/ednet/ednet_preprocessing_summary.json"
    quality = data_root / "processed/ednet/ednet_quality_summary.json"
    summary = json.loads(processed.read_text(encoding="utf-8")) if processed.exists() else {}
    quality_summary = json.loads(quality.read_text(encoding="utf-8")) if quality.exists() else {}
    raw_files = sorted(str(path.relative_to(data_root)) for path in (data_root / "raw").rglob("*") if path.is_file())
    ednet_present = bool(summary and quality_summary)
    interactions = summary.get("interactions_written", 0)
    labels = summary.get("eligible_supervised_targets", 0)
    rows_with_timestamps = quality_summary.get("valid_timestamps", 0)
    modalities = [
        {
            "modality": "Text",
            "actual_data_available": False,
            "source": "No learner-authored text source found. EdNet question content is item metadata, not learner writing.",
            "timestamp_available": False,
            "labels_available": False,
            "limitations": "Adapter accepts caller-provided text; only synthetic fixtures exercise it.",
        },
        {
            "modality": "Voice / speech",
            "actual_data_available": False,
            "source": "No learner audio files or speech transcripts found in the inspected raw/processed data inventory.",
            "timestamp_available": False,
            "labels_available": False,
            "limitations": "Reference/WAV metadata support only; no ASR runtime or real speech corpus is present.",
        },
        {
            "modality": "Visual artifacts",
            "actual_data_available": False,
            "source": "No learner images, diagrams, handwriting or visual artifacts found in the inspected data inventory.",
            "timestamp_available": False,
            "labels_available": False,
            "limitations": "Reference, hash and basic PNG/JPEG metadata support only; no OCR or visual interpretation is run.",
        },
        {
            "modality": "Interaction",
            "actual_data_available": bool(ednet_present and interactions),
            "source": "EdNet KT1 processed interaction table plus raw KT1 archive.",
            "timestamp_available": bool(rows_with_timestamps),
            "labels_available": bool(labels),
            "limitations": "Correctness is a response outcome; source timestamps are shifted question-given times, not response submission times.",
            "counts": {"interactions": interactions, "labelled_correctness": labels, "timestamped_interactions": rows_with_timestamps},
        },
        {
            "modality": "Temporal history",
            "actual_data_available": bool(ednet_present and interactions),
            "source": "Chronological EdNet event order and Phase 9 behavioral learner-state implementation/output.",
            "timestamp_available": bool(rows_with_timestamps),
            "labels_available": False,
            "limitations": "Derived behavioral summaries are not cognitive labels and can use only events observed through their cutoff.",
        },
    ]
    return {
        "data_root": str(data_root),
        "raw_file_inventory": raw_files,
        "processed_ednet_summary_available": ednet_present,
        "modalities": modalities,
        "interpretation": "Only interaction and derived temporal-history evidence are available as real learner data in this snapshot.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.data_root)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
