from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.ednet_preprocessing import (  # noqa: E402
    FEATURE_COLUMNS,
    assert_no_target_leakage,
    process_learner_rows,
    split_unseen_learner,
    temporal_split_for_position,
)


CONTENT = {
    "q1": {"question_id": "q1", "correct_answer": "a", "tags": "10;11", "part": "1"},
    "q2": {"question_id": "q2", "correct_answer": "b", "tags": "10", "part": "2"},
}


def row(timestamp, solving_id, question_id, answer, elapsed):
    return {
        "timestamp": str(timestamp),
        "solving_id": str(solving_id),
        "question_id": question_id,
        "user_answer": answer,
        "elapsed_time": str(elapsed),
    }


class EdNetPreprocessingTests(unittest.TestCase):
    def test_ties_preserve_source_order_and_duplicate_is_flagged_not_removed(self):
        raw = [
            row(1000, 1, "q1", "a", 500),
            row(2000, 2, "q2", "c", 600),
            row(2000, 2, "q2", "c", 600),
        ]
        processed, stats = process_learner_rows("u1", raw, CONTENT)
        self.assertEqual([item["source_row_order"] for item in processed], [0, 1, 2])
        self.assertEqual([item["timestamp"] for item in processed], ["1000", "2000", "2000"])
        self.assertEqual([item["is_exact_duplicate"] for item in processed], [False, False, True])
        self.assertEqual(stats["exact_duplicate_rows"], 1)
        self.assertEqual(len(processed), len(raw))

    def test_blank_answer_is_unlabelled_but_remains_a_historical_logged_event(self):
        raw = [row(1000, 1, "q1", "a", 500), row(2000, 2, "q2", "", 700), row(3000, 3, "q2", "b", 800)]
        processed, stats = process_learner_rows("u1", raw, CONTENT)
        self.assertEqual(processed[1]["correctness"], None)
        self.assertEqual(processed[1]["split_unseen_learner"], "")
        self.assertEqual(processed[2]["n_prior_logged_events"], 2)
        self.assertEqual(processed[2]["n_prior_answered_attempts"], 1)
        self.assertEqual(processed[2]["n_prior_correct"], 1)
        self.assertEqual(stats["blank_answers"], 1)
        self.assertEqual(stats["eligible_targets"], 2)

    def test_target_and_history_feature_generation_do_not_leak_current_answer(self):
        raw = [row(1000, 1, "q1", "a", 500), row(2000, 2, "q2", "c", 600)]
        changed = [raw[0], {**raw[1], "user_answer": "b"}]
        original_rows, _ = process_learner_rows("u1", raw, CONTENT)
        changed_rows, _ = process_learner_rows("u1", changed, CONTENT)
        self.assertEqual(original_rows[1]["correctness"], 0)
        self.assertEqual(changed_rows[1]["correctness"], 1)
        self.assertEqual(
            {key: original_rows[1][key] for key in FEATURE_COLUMNS},
            {key: changed_rows[1][key] for key in FEATURE_COLUMNS},
        )
        self.assertEqual(original_rows[1]["n_prior_correct"], 1)
        self.assertEqual(original_rows[1]["prior_skill_tag_attempts"], 1)

    def test_cold_start_and_learner_state_isolation(self):
        first, _ = process_learner_rows("u1", [row(1000, 1, "q1", "a", 500)], CONTENT)
        other, _ = process_learner_rows("u2", [row(2000, 1, "q2", "b", 700)], CONTENT)
        self.assertEqual(first[0]["n_prior_answered_attempts"], 0)
        self.assertIsNone(first[0]["prior_accuracy"])
        self.assertEqual(other[0]["n_prior_answered_attempts"], 0)
        self.assertIsNone(other[0]["previous_response_correctness"])

    def test_split_reproducibility_and_temporal_integrity(self):
        self.assertEqual(split_unseen_learner("u123", 2025), split_unseen_learner("u123", 2025))
        raw = [row(1000 + index, index, "q1" if index % 2 == 0 else "q2", "a" if index % 2 == 0 else "b", 500) for index in range(10)]
        first, _ = process_learner_rows("u123", raw, CONTENT, seed=2025)
        again, _ = process_learner_rows("u123", raw, CONTENT, seed=2025)
        self.assertEqual(first, again)
        self.assertEqual({item["split_unseen_learner"] for item in first}, {split_unseen_learner("u123", 2025)})
        future = [item["split_future_known_learner"] for item in first]
        self.assertEqual(future, ["train"] * 7 + ["validation", "test", "test"])
        self.assertEqual(temporal_split_for_position(0, 10), "train")
        self.assertEqual(temporal_split_for_position(6, 10), "train")
        self.assertEqual(temporal_split_for_position(7, 10), "validation")
        self.assertEqual(temporal_split_for_position(8, 10), "test")
        self.assertEqual(temporal_split_for_position(0, 1), "train")

    def test_feature_whitelist_rejects_target_and_post_response_fields(self):
        assert_no_target_leakage()
        with self.assertRaises(ValueError):
            assert_no_target_leakage((*FEATURE_COLUMNS, "correctness"))
        self.assertNotIn("submitted_answer", FEATURE_COLUMNS)
        self.assertNotIn("correct_answer", FEATURE_COLUMNS)
        self.assertNotIn("elapsed_time_ms", FEATURE_COLUMNS)

    def test_decreasing_timestamp_fails_instead_of_reordering(self):
        raw = [row(2000, 1, "q1", "a", 500), row(1000, 2, "q2", "b", 600)]
        with self.assertRaisesRegex(ValueError, "will not reorder"):
            process_learner_rows("u1", raw, CONTENT)


if __name__ == "__main__":
    unittest.main()
