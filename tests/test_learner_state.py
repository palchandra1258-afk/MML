from __future__ import annotations

import json
import sys
import csv
import gzip
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.learner_state.state_builder import (  # noqa: E402
    LearnerStateAccumulator,
    build_state_from_rows,
    skill_ids,
    wilson_interval,
)
from mcp_ri.learner_state.state_schema import SCHEMA_PATH, validate_state  # noqa: E402


def row(order: int, label: str = "1", tags: str = "7", *, timestamp: int | None = None,
        duplicate: str = "0", question: str | None = None) -> dict[str, str]:
    return {
        "learner_id": "u-test",
        "source_row_order": str(order),
        "timestamp": str(timestamp if timestamp is not None else 1000 + order),
        "question_id": question or f"q{order + 1}",
        "correctness": label,
        "skill_tags": tags,
        "is_exact_duplicate": duplicate,
    }


def one_concept(state: dict, concept_id: str = "ednet_skill:7") -> dict:
    return next(item for item in state["concept_states"] if item["concept_id"] == concept_id)


class LearnerStateTests(unittest.TestCase):
    def test_empty_learner_history(self):
        state = build_state_from_rows("u-empty", [])
        self.assertEqual(state["observation_summary"]["total_interactions"], 0)
        self.assertIsNone(state["learning_performance"]["historical_performance"])
        self.assertEqual(state["learning_performance"]["uncertainty_interval_95"], [0.0, 1.0])
        validate_state(state)

    def test_one_interaction(self):
        state = build_state_from_rows("u-test", [row(0)])
        self.assertEqual(state["learning_performance"]["historical_performance"], 1.0)
        self.assertEqual(one_concept(state)["attempts"], 1)

    def test_multiple_correct_responses(self):
        state = build_state_from_rows("u-test", [row(i, "1") for i in range(4)])
        self.assertEqual(one_concept(state)["correct"], 4)
        self.assertEqual(one_concept(state)["incorrect"], 0)

    def test_multiple_incorrect_responses(self):
        state = build_state_from_rows("u-test", [row(i, "0") for i in range(4)])
        self.assertEqual(one_concept(state)["incorrect"], 4)
        self.assertIn("repeated_recent_incorrect_responses", one_concept(state)["potential_issues"])

    def test_mixed_responses(self):
        state = build_state_from_rows("u-test", [row(i, "1" if i % 2 else "0") for i in range(6)])
        concept = one_concept(state)
        self.assertEqual((concept["correct"], concept["incorrect"]), (3, 3))
        self.assertIn("inconsistent_recent_responses", concept["potential_issues"])

    def test_multiple_skills_per_question_are_each_updated_once(self):
        state = build_state_from_rows("u-test", [row(0, "1", "7;8;7")])
        self.assertEqual([c["concept_id"] for c in state["concept_states"]],
                         ["ednet_skill:7", "ednet_skill:8"])
        self.assertEqual([c["attempts"] for c in state["concept_states"]], [1, 1])

    def test_missing_skill_mappings_still_count_as_interactions(self):
        state = build_state_from_rows("u-test", [row(0, "1", "-1")])
        self.assertEqual(state["observation_summary"]["total_interactions"], 1)
        self.assertEqual(state["observation_summary"]["interactions_without_skill_mapping"], 1)
        self.assertEqual(state["concept_states"], [])
        self.assertEqual(skill_ids(""), ())

    def test_missing_answers_remain_unlabelled_and_do_not_update_performance(self):
        state = build_state_from_rows("u-test", [row(0, "")])
        self.assertEqual(state["observation_summary"]["unlabelled_interactions"], 1)
        self.assertEqual(state["learning_performance"]["attempts"], 0)
        self.assertEqual(one_concept(state)["attempts"], 0)

    def test_duplicate_interactions_are_preserved_as_separate_observations(self):
        state = build_state_from_rows("u-test", [row(0, "1"), row(1, "1", duplicate="1")])
        self.assertEqual(state["observation_summary"]["total_interactions"], 2)
        self.assertEqual(state["observation_summary"]["preserved_duplicate_interactions"], 1)
        self.assertEqual(one_concept(state)["attempts"], 2)

    def test_insufficient_evidence_is_explicit(self):
        state = build_state_from_rows("u-test", [row(0, "1")])
        concept = one_concept(state)
        self.assertEqual(concept["evidence_sufficiency"], "low")
        self.assertEqual(concept["estimate_confidence"], "low")
        self.assertEqual(concept["uncertainty_level"], "high")
        self.assertIn("insufficient_evidence", concept["potential_issues"])

    def test_recent_performance_change_is_detected(self):
        labels = ["1"] * 5 + ["0"] * 5
        state = build_state_from_rows("u-test", [row(i, label) for i, label in enumerate(labels)])
        self.assertEqual(state["learning_performance"]["performance_trend"], "declining")
        self.assertAlmostEqual(state["learning_performance"]["performance_change"], -1.0)

    def test_temporal_ordering_rejects_decreasing_timestamp(self):
        accumulator = LearnerStateAccumulator("u-test")
        accumulator.update(row(0, timestamp=2000))
        with self.assertRaisesRegex(ValueError, "nondecreasing"):
            accumulator.update(row(1, timestamp=1000))

    def test_temporal_ordering_rejects_repeated_source_order(self):
        accumulator = LearnerStateAccumulator("u-test")
        accumulator.update(row(1))
        with self.assertRaisesRegex(ValueError, "strictly increase"):
            accumulator.update(row(1))

    def test_historical_state_reconstruction_from_prefix(self):
        history = [row(i, "1" if i < 2 else "0") for i in range(4)]
        early = build_state_from_rows("u-test", history[:2])
        final = build_state_from_rows("u-test", history)
        self.assertEqual(early["learning_performance"]["historical_performance"], 1.0)
        self.assertEqual(final["learning_performance"]["historical_performance"], 0.5)
        self.assertEqual(early["observation_summary"]["total_interactions"], 2)

    def test_beta_binomial_smoothing_matches_uniform_prior(self):
        state = build_state_from_rows("u-test", [row(0, "1"), row(1, "0")])
        self.assertAlmostEqual(one_concept(state)["smoothed_performance"], 0.5)
        single = build_state_from_rows("u-test", [row(0, "1")])
        self.assertAlmostEqual(one_concept(single)["smoothed_performance"], 2 / 3)

    def test_json_schema_validation_and_rejects_invalid_counts(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
        state = build_state_from_rows("u-test", [row(0)])
        validate_state(state)
        state["concept_states"][0]["attempts"] = -1
        with self.assertRaises(ValueError):
            validate_state(state)

    def test_future_rows_do_not_change_a_historical_prefix_state(self):
        prefix = [row(i, "1") for i in range(5)]
        future = row(5, "0")
        state_before = build_state_from_rows("u-test", prefix)
        state_after = build_state_from_rows("u-test", prefix + [future])
        self.assertEqual(state_before["learning_performance"]["historical_performance"], 1.0)
        self.assertEqual(state_after["learning_performance"]["historical_performance"], 5 / 6)
        self.assertEqual(state_before["state_timestamp"], prefix[-1]["timestamp"])

    def test_more_evidence_narrows_wilson_interval(self):
        few = wilson_interval(4, 5)
        many = wilson_interval(80, 100)
        self.assertLess(many[1] - many[0], few[1] - few[0])

    def test_prediction_is_separate_and_does_not_change_performance_estimate(self):
        accumulator = LearnerStateAccumulator("u-test")
        accumulator.update(row(0, "1"))
        before = accumulator.snapshot()
        accumulator.set_next_response_prediction(0.73, "verified-test-double")
        after = accumulator.snapshot()
        self.assertEqual(after["learning_performance"], before["learning_performance"])
        self.assertEqual(after["model_predictions"]["next_response_correctness"], 0.73)
        self.assertIn("not an understanding estimate", after["model_predictions"]["reason"])

    def test_streaming_validation_export_includes_unlabelled_rows_but_skips_other_splits(self):
        from scripts.learner_state.build_and_evaluate import run
        from mcp_ri.ednet_preprocessing import split_unseen_learner

        validation_id = next(f"u{i}" for i in range(1000)
                             if split_unseen_learner(f"u{i}", 2025) == "validation")
        train_id = next(f"u{i}" for i in range(1000)
                        if split_unseen_learner(f"u{i}", 2025) == "train")
        fields = ["learner_id", "source_row_order", "timestamp", "question_id", "correctness",
                  "skill_tags", "split_unseen_learner", "is_exact_duplicate"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "processed.csv.gz"
            with gzip.open(dataset, "wt", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"learner_id": train_id, "source_row_order": 0, "timestamp": 1000,
                                 "question_id": "q1", "correctness": "1", "skill_tags": "1",
                                 "split_unseen_learner": "train", "is_exact_duplicate": 0})
                writer.writerow({"learner_id": validation_id, "source_row_order": 0, "timestamp": 1000,
                                 "question_id": "q1", "correctness": "", "skill_tags": "1",
                                 "split_unseen_learner": "", "is_exact_duplicate": 0})
                writer.writerow({"learner_id": validation_id, "source_row_order": 1, "timestamp": 1001,
                                 "question_id": "q2", "correctness": "0", "skill_tags": "1",
                                 "split_unseen_learner": "validation", "is_exact_duplicate": 0})
            (root / "ednet_preprocessing_summary.json").write_text(json.dumps({"seed": 2025}))
            output = root / "output"
            report = run(dataset, output)
            states = [json.loads(line) for line in
                      (output / "validation_learner_states.jsonl").read_text().splitlines()]
        self.assertEqual(report["status"], "complete")
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["learner_id"], validation_id)
        self.assertEqual(states[0]["observation_summary"]["total_interactions"], 2)
        self.assertEqual(states[0]["observation_summary"]["unlabelled_interactions"], 1)
        self.assertFalse(report["locked_test_partition_read_for_labels_or_state"])


if __name__ == "__main__":
    unittest.main()
