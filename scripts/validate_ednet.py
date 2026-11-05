#!/usr/bin/env python3
"""Validate acquired EdNet KT1 and question-content archives and write reports."""

from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.ednet_validation import inspect_archives, write_reports  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(os.environ.get("MCP_RI_DATA_DIR", ROOT / "data")),
        help="dataset root (default: MCP_RI_DATA_DIR or repository data/)",
    )
    args = parser.parse_args()
    raw = args.data_root.expanduser() / "raw" / "ednet"
    kt1 = raw / "ednet-kt1.zip"
    content = raw / "ednet-content.zip"
    for path in (kt1, content):
        if not path.is_file():
            print(f"Required archive is missing: {path}", file=sys.stderr)
            return 2
        if not zipfile.is_zipfile(path):
            print(f"Archive integrity check failed (not a ZIP): {path}", file=sys.stderr)
            return 2
    try:
        summary = inspect_archives(kt1, content)
        report_dir = args.data_root.expanduser() / "processed" / "ednet"
        import json

        kt1_meta = json.loads((raw / "ednet-kt1.zip.metadata.json").read_text())
        content_meta = json.loads((raw / "ednet-content.zip.metadata.json").read_text())
        summary["acquisition"] = {
            "kt1_size_bytes": kt1.stat().st_size,
            "kt1_sha256": kt1_meta["sha256"],
            "content_size_bytes": content.stat().st_size,
            "content_sha256": content_meta["sha256"],
        }
        outputs = write_reports(summary, report_dir, ROOT / "docs")
    except Exception as exc:
        print(f"Validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    for output in outputs:
        print(output)
    print(f"Learners={summary['learner_files']:,}; interactions={summary['interaction_rows']:,}")
    print(f"Prediction task structurally supported: {summary['prediction_task_supported']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
