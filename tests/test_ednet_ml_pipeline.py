from __future__ import annotations

import importlib.util
import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if importlib.util.find_spec("sklearn") is None:
    raise unittest.SkipTest("install requirements-training.txt to run ML pipeline tests")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.linear_model import SGDClassifier  # noqa: E402

from mcp_ri.models.ednet_logistic import (  # noqa: E402
    SparseFeatureEncoder,
    assert_training_feature_whitelist,
    classification_metrics,
    row_is_training_sample,
)
sys.path.insert(0, str(ROOT / "scripts" / "training"))
from train_ednet_baselines import main as train_main  # noqa: E402
from mcp_ri.ednet_preprocessing import FEATURE_COLUMNS, output_columns  # noqa: E402


class EdNetMLPipelineTests(unittest.TestCase):
    def base_row(self, **overrides):
        row = {
            "current_question_id": "q1",
            "current_part": "1",
            "current_skill_tags": "10;11",
            "n_prior_logged_events": "0",
            "n_prior_answered_attempts": "0",
            "n_prior_correct": "0",
            "prior_accuracy": "",
            "recent_5_accuracy": "",
            "recent_10_accuracy": "",
            "recent_accuracy_trend_5": "",
            "previous_response_correctness": "",
            "previous_elapsed_time_ms": "",
            "gap_since_previous_question_ms": "",
            "prior_skill_tag_attempts": "0",
            "prior_skill_tag_correct": "0",
            "prior_skill_tag_accuracy": "0.0",
        }
        row.update(overrides)
        return row

    def test_feature_whitelist_enforcement_and_target_fields_ignored(self):
        assert_training_feature_whitelist()
        encoder = SparseFeatureEncoder()
        encoder.fit_batch([self.base_row()])
        encoder.finalize()
        first, _ = encoder.transform([self.base_row(submitted_answer="a", correct_answer="a", correctness="1")])
        changed, _ = encoder.transform([self.base_row(submitted_answer="d", correct_answer="b", correctness="0")])
        np.testing.assert_array_equal(first.toarray(), changed.toarray())

    def test_encoder_fit_is_train_only_and_unknown_categories_are_stable(self):
        encoder = SparseFeatureEncoder()
        encoder.fit_batch([self.base_row()])
        encoder.finalize()
        known, _ = encoder.transform([self.base_row()])
        unknown, unknown_counts = encoder.transform([
            self.base_row(current_question_id="q_unseen", current_part="9", current_skill_tags="999")
        ])
        self.assertEqual(known.shape, unknown.shape)
        self.assertEqual(unknown_counts, {"question_id": 1, "part": 1, "skill_tag": 1})
        self.assertEqual(encoder.question_index, {"q1": 0})

    def test_training_sample_keeps_learner_and_split_integrity(self):
        rows = [
            {"learner_id": "u1", "split_unseen_learner": "train", "correctness": "1"},
            {"learner_id": "u1", "split_unseen_learner": "train", "correctness": "0"},
            {"learner_id": "u1", "split_unseen_learner": "validation", "correctness": "1"},
            {"learner_id": "u2", "split_unseen_learner": "test", "correctness": "0"},
        ]
        selected = [row_is_training_sample(row, seed=2025, sample_percent=100) for row in rows]
        self.assertEqual(selected, [True, True, False, False])

    def test_cold_start_encoder_and_logistic_prediction_are_finite(self):
        encoder = SparseFeatureEncoder()
        train = [
            self.base_row(n_prior_logged_events=str(i), n_prior_answered_attempts=str(i), n_prior_correct=str(i % 2), prior_accuracy=str(i % 2))
            for i in range(20)
        ]
        encoder.fit_batch(train)
        encoder.finalize()
        x, _ = encoder.transform(train)
        y = np.array([0, 1] * 10, dtype=np.int8)
        model = SGDClassifier(loss="log_loss", random_state=3, max_iter=1, tol=None)
        model.partial_fit(x, y, classes=np.array([0, 1], dtype=np.int8))
        cold, _ = encoder.transform([self.base_row()])
        probability = model.predict_proba(cold)[0, 1]
        self.assertTrue(np.isfinite(probability))
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

    def test_reproducible_training_and_model_save_load(self):
        encoder = SparseFeatureEncoder()
        rows = [self.base_row(n_prior_logged_events=str(i), n_prior_answered_attempts=str(i), prior_accuracy=str(i % 2)) for i in range(20)]
        encoder.fit_batch(rows)
        encoder.finalize()
        x, _ = encoder.transform(rows)
        y = np.array([0, 1] * 10, dtype=np.int8)
        first = SGDClassifier(loss="log_loss", random_state=4, max_iter=1, tol=None)
        second = SGDClassifier(loss="log_loss", random_state=4, max_iter=1, tol=None)
        first.partial_fit(x, y, classes=np.array([0, 1], dtype=np.int8))
        second.partial_fit(x, y, classes=np.array([0, 1], dtype=np.int8))
        np.testing.assert_array_equal(first.coef_, second.coef_)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.joblib"
            joblib.dump(first, path)
            loaded = joblib.load(path)
            np.testing.assert_allclose(first.predict_proba(x), loaded.predict_proba(x))
            encoder_path = Path(tmp) / "encoder.json"
            encoder.save(encoder_path)
            loaded_encoder = SparseFeatureEncoder.load(encoder_path)
            np.testing.assert_array_equal(encoder.transform(rows)[0].toarray(), loaded_encoder.transform(rows)[0].toarray())

    def test_metrics_calculation(self):
        result = classification_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.6, 0.9]))
        self.assertEqual(result["n_examples"], 4)
        self.assertEqual(result["confusion_matrix_true_rows_pred_columns_labels_0_1"], [[2, 0], [0, 2]])
        self.assertEqual(result["roc_auc"], 1.0)
        self.assertEqual(len(result["calibration_bins"]), 15)

    def test_training_script_integration_saves_artifacts_and_uses_validation_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data_dir = root / "data" / "processed" / "ednet"
            data_dir.mkdir(parents=True)
            dataset = data_dir / "ednet_kt1_features.csv.gz"
            fields = output_columns()
            with gzip.open(dataset, "wt", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for index in range(40):
                    writer.writerow(self._training_row(index, "train"))
                for index in range(20):
                    writer.writerow(self._training_row(index + 40, "validation"))
                for index in range(5):
                    writer.writerow(self._training_row(index + 60, "test"))
            summary = {
                "source_archives": {"kt1": {"sha256": "fixture"}},
                "split_protocols": {"unseen_learner": {"train": {
                    "targets": 40, "correct_targets": 20, "incorrect_targets": 20,
                }}},
            }
            (data_dir / "ednet_preprocessing_summary.json").write_text(json.dumps(summary))
            output_root = root / "artifacts"
            status = train_main([
                "--data-root", str(root / "data"), "--output-root", str(output_root),
                "--sample-percent", "100", "--epochs", "1", "--batch-size", "10",
            ])
            self.assertEqual(status, 0)
            report_path = output_root / "results" / "reports" / "ednet_logistic_experiment.json"
            report = json.loads(report_path.read_text())
            self.assertEqual(report["status"], "complete")
            self.assertIn("validation only", report["split_protocol"])
            self.assertIn("test split not evaluated", report["split_protocol"])
            self.assertEqual(report["training_configuration"]["validation_examples"], 20)
            self.assertTrue((output_root / "models" / "trained" / "ednet_sgd_logistic.joblib").is_file())
            self.assertTrue((output_root / "models" / "preprocessing" / "ednet_sgd_preprocessor.json").is_file())

    def _training_row(self, index: int, split: str):
        label = str(index % 2)
        row = {column: "" for column in output_columns()}
        row.update({
            "learner_id": f"u_{split}_{index}",
            "source_row_order": "0",
            "timestamp": str(index + 1000),
            "question_id": "q1" if index % 3 else "q2",
            "submitted_answer": "a" if label == "1" else "b",
            "correct_answer": "a",
            "correctness": label,
            "skill_tags": "10;11",
            "session_id": str(index),
            "source_dataset": "EdNet-KT1",
            "elapsed_time_ms": "1000",
            "is_exact_duplicate": "0",
            "split_unseen_learner": split,
            "split_future_known_learner": split,
            "current_question_id": "q1" if index % 3 else "q2",
            "current_part": "1",
            "current_skill_tags": "10;11",
            "n_prior_logged_events": str(index),
            "n_prior_answered_attempts": str(index),
            "n_prior_correct": str(index // 2),
            "prior_accuracy": "0.5",
            "recent_5_accuracy": "0.5",
            "recent_10_accuracy": "0.5",
            "recent_accuracy_trend_5": "0.0",
            "previous_response_correctness": label,
            "previous_response_skill_tags": "10;11",
            "previous_elapsed_time_ms": "900",
            "gap_since_previous_question_ms": "1000",
            "prior_skill_tag_attempts": str(index),
            "prior_skill_tag_correct": str(index // 2),
            "prior_skill_tag_accuracy": "0.5",
        })
        return row


if __name__ == "__main__":
    unittest.main()
