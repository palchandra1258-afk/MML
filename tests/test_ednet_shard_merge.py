from __future__ import annotations

import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from merge_ednet_shards import merge  # noqa: E402


def make_summary(output: Path, start: int, end: int, *, header: bool) -> dict:
    return {
        "seed": 2025,
        "source_archives": {"kt1": {"sha256": "same"}},
        "model_feature_columns": ["prior_accuracy"],
        "output_columns": ["learner_id", "correctness", "split_unseen_learner", "split_future_known_learner"],
        "learner_index_start": start,
        "learner_index_end_exclusive": end,
        "output": {"path": str(output)},
        "learner_limit": None,
        "learners_processed": 1,
        "interactions_written": 1,
        "eligible_supervised_targets": 1,
        "blank_answers_excluded_as_targets": 0,
        "invalid_answers_excluded_as_targets": 0,
        "unlabelled_nonblank_answers": 0,
        "exact_duplicate_rows_preserved": 0,
        "unmatched_question_ids": 0,
        "invalid_question_ids": 0,
        "invalid_timestamps": 0,
        "unavailable_elapsed_time": 0,
        "missing_skill_tag_rows": 0,
        "blank_raw_fields": {},
        "split_protocols": {
            protocol: {
                split: {"learners": int(split == "train"), "targets": int(split == "train"), "correct_targets": int(split == "train"), "incorrect_targets": 0}
                for split in ("train", "validation", "test")
            }
            for protocol in ("unseen_learner", "future_known_learner")
        },
        "header_written": header,
    }


class EdNetShardMergeTests(unittest.TestCase):
    def test_ordered_gzip_shards_merge_to_one_csv_header_and_aggregate_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            header = "learner_id,correctness,split_unseen_learner,split_future_known_learner\n"
            a = root / "a.csv.gz"
            b = root / "b.csv.gz"
            with gzip.open(a, "wt", newline="") as stream:
                stream.write(header + "u1,1,train,train\n")
            with gzip.open(b, "wt", newline="") as stream:
                stream.write("u2,0,train,train\n")
            s1, s2 = root / "a.json", root / "b.json"
            s1.write_text(json.dumps(make_summary(a, 0, 1, header=True)))
            s2.write_text(json.dumps(make_summary(b, 1, 2, header=False)))
            output, summary_output = root / "all.csv.gz", root / "all.json"
            summary = merge([s1, s2], output, summary_output)
            with gzip.open(output, "rt", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([row["learner_id"] for row in rows], ["u1", "u2"])
            self.assertEqual(summary["learners_processed"], 2)
            self.assertEqual(summary["interactions_written"], 2)
            self.assertEqual(summary["split_protocols"]["unseen_learner"]["train"]["targets"], 2)


if __name__ == "__main__":
    unittest.main()
