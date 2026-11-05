import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from scripts.training.train_ednet_sequence_models import (
    SequenceRecord,
    build_model,
    model_logits,
    predict_sequences,
)
from mcp_ri.models.ednet_logistic import (
    assert_training_feature_whitelist,
    classification_metrics,
)


class SequenceModelTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)

    def _inputs(self):
        questions = torch.tensor([[1, 3, 4, 2]], dtype=torch.long)
        answers = torch.tensor([[1, 0, 1, 0]], dtype=torch.long)
        target_questions = questions[:, 1:]
        lengths = torch.tensor([4], dtype=torch.long)
        return questions, answers, target_questions, lengths

    def test_checkpoint_round_trip_preserves_logits(self):
        for name in ("dkt", "sakt"):
            with self.subTest(model=name):
                torch.manual_seed(31)
                original = build_model(name, n_items=8, max_length=4).eval()
                q, y, target_q, lengths = self._inputs()
                expected = original(q[:, :-1], y[:, :-1], target_q, lengths)
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "model.pt"
                    torch.save({"state_dict": original.state_dict()}, path)
                    restored = build_model(name, n_items=8, max_length=4).eval()
                    payload = torch.load(path, map_location="cpu", weights_only=True)
                    restored.load_state_dict(payload["state_dict"])
                    actual = restored(q[:, :-1], y[:, :-1], target_q, lengths)
                torch.testing.assert_close(actual, expected)

    def test_initialization_is_reproducible_for_fixed_seed(self):
        for name in ("dkt", "sakt"):
            with self.subTest(model=name):
                torch.manual_seed(2025)
                first = build_model(name, n_items=8, max_length=4)
                torch.manual_seed(2025)
                second = build_model(name, n_items=8, max_length=4)
                for left, right in zip(first.parameters(), second.parameters()):
                    torch.testing.assert_close(left, right)

    def test_future_responses_do_not_change_earlier_prediction(self):
        q, y, target_q, lengths = self._inputs()
        changed_q = q.clone()
        changed_y = y.clone()
        changed_q[:, 2:] = torch.tensor([[6, 5]])
        changed_y[:, 1:] = torch.tensor([[1, 0, 1]])
        for name in ("dkt", "sakt"):
            with self.subTest(model=name):
                torch.manual_seed(17)
                model = build_model(name, n_items=8, max_length=4).eval()
                with torch.no_grad():
                    original = model_logits(model, name, q, y, lengths)
                    changed = model_logits(model, name, changed_q, changed_y, lengths)
                # Position zero predicts q[1] from q[0], y[0]. Changed fields
                # belong to the target response or later interactions.
                torch.testing.assert_close(original[:, 0], changed[:, 0])

    def test_predict_sequences_returns_one_prediction_per_transition(self):
        for name in ("dkt", "sakt"):
            with self.subTest(model=name):
                torch.manual_seed(11)
                model = build_model(name, n_items=8, max_length=4).eval()
                record = SequenceRecord(
                    questions=np.asarray([1, 3, 4, 2, 5], dtype=np.uint16),
                    answers=np.asarray([1, 0, 1, 0, 1], dtype=np.int8),
                    role=2,
                    offset=0,
                )
                probabilities, windows = predict_sequences(
                    model, name, [record], n_rows=5, batch_size=2,
                    max_length=4, device=torch.device("cpu"),
                )
                self.assertEqual(windows, 2)
                self.assertTrue(np.isnan(probabilities[0]))
                self.assertTrue(np.isfinite(probabilities[1:]).all())
                self.assertTrue(((probabilities[1:] >= 0) &
                                 (probabilities[1:] <= 1)).all())

    def test_feature_whitelist_and_metric_contract(self):
        assert_training_feature_whitelist()
        y = np.asarray([0, 1, 1, 0], dtype=np.int8)
        probability = np.asarray([0.1, 0.7, 0.5, 0.9], dtype=np.float64)
        metrics = classification_metrics(y, probability)
        for key in ("accuracy", "precision_positive_correct",
                    "recall_positive_correct", "f1_positive_correct",
                    "roc_auc", "pr_auc_average_precision", "log_loss",
                    "brier_score", "ece_equal_width"):
            self.assertIn(key, metrics)
            self.assertTrue(np.isfinite(metrics[key]))

    def test_learner_role_assignment_is_deterministic(self):
        from scripts.training.train_ednet_sequence_models import learner_role

        self.assertEqual(learner_role("learner-123", 2025),
                         learner_role("learner-123", 2025))
        self.assertNotEqual(learner_role("learner-123", 2025),
                            learner_role("learner-123", 2026))


if __name__ == "__main__":
    unittest.main()
