from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.cognitive_state import CognitiveStateHistory, estimate_cognitive_state, validate_cognitive_state  # noqa: E402
from mcp_ri.evidence.adapters.interaction import InteractionAdapter  # noqa: E402
from mcp_ri.evidence.adapters.temporal import TemporalHistoryAdapter  # noqa: E402
from mcp_ri.evidence.adapters.text import TextAdapter  # noqa: E402
from mcp_ri.evidence.adapters.audio import AudioAdapter  # noqa: E402
from mcp_ri.evidence.adapters.visual import VisualAdapter  # noqa: E402
from mcp_ri.evidence.evidence_schema import validate_evidence  # noqa: E402
from mcp_ri.evidence.registry import EvidenceRegistry  # noqa: E402
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402


def make_bundle(labels: list[int], *, learner: str = "u-cognitive"):
    accumulator = LearnerStateAccumulator(learner)
    adapter = InteractionAdapter()
    records = []
    for order, label in enumerate(labels):
        row = {
            "learner_id": learner,
            "source_row_order": str(order),
            "timestamp": str(1_000_000 + order * 1_000),
            "question_id": f"q{order + 1}",
            "solving_id": f"solve-{order}",
            "submitted_answer": "a" if label else "b",
            "correctness": str(label),
            "skill_tags": "7",
            "session_id": "session-1",
            "is_exact_duplicate": "0",
        }
        records.append(adapter.from_processed_row(row))
        accumulator.update(row)
    state = accumulator.snapshot()
    temporal = TemporalHistoryAdapter().from_learner_state(
        state,
        state_reference=f"test-prefix:{learner}:{len(labels)}",
        related_evidence_ids=[record["evidence_id"] for record in records],
    )
    records.append(temporal)
    return state, records, accumulator


def write_png(path: Path) -> None:
    def chunk(name: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + chunk(b"IEND", b""))


class CognitiveStateTests(unittest.TestCase):
    def test_sparse_evidence_is_insufficient_and_requests_a_diagnostic(self):
        phase9, evidence, _ = make_bundle([1, 0])
        state = estimate_cognitive_state(phase9, evidence)
        validate_cognitive_state(state)
        estimate, = state["concept_estimates"]
        self.assertEqual(estimate["estimated_learning_status"], "insufficient_evidence")
        self.assertEqual(estimate["estimate_confidence"], "low")
        self.assertEqual(estimate["evidence_sufficiency"], "low")
        self.assertEqual(state["diagnostic_recommendations"][0]["action"], "present_diagnostic_question")
        self.assertEqual(state["uncertainty"]["inference_uncertainty"], "high")
        self.assertEqual(state["uncertainty"]["modality_uncertainty"], "high")

    def test_repeated_incorrect_responses_produce_a_hypothesis_not_a_diagnosis(self):
        phase9, evidence, _ = make_bundle([0] * 5)
        state = estimate_cognitive_state(phase9, evidence)
        estimate, = state["concept_estimates"]
        self.assertEqual(estimate["estimated_learning_status"], "possible_difficulty")
        self.assertTrue(any(h["hypothesis_type"] == "repeated_incorrect_responses" for h in state["possible_difficulty_hypotheses"]))
        self.assertFalse(any("misconception" in h["hypothesis_type"] for h in state["possible_difficulty_hypotheses"]))
        self.assertIn("may require further investigation", estimate["rationale"])

    def test_declining_performance_hypothesis_uses_phase9_trend(self):
        phase9, evidence, _ = make_bundle([1] * 5 + [0] * 5)
        state = estimate_cognitive_state(phase9, evidence)
        estimate, = state["concept_estimates"]
        self.assertEqual(estimate["observed_performance"]["performance_trend"], "declining")
        self.assertEqual(estimate["estimated_learning_status"], "possible_difficulty")
        self.assertTrue(any(h["hypothesis_type"] == "declining_recent_performance" for h in state["possible_difficulty_hypotheses"]))

    def test_high_consistent_response_pattern_uses_documented_rule(self):
        phase9, evidence, _ = make_bundle([1] * 20)
        state = estimate_cognitive_state(phase9, evidence)
        estimate, = state["concept_estimates"]
        self.assertEqual(estimate["estimated_learning_status"], "relatively_consistent_performance")
        self.assertEqual(estimate["estimate_confidence"], "low")
        self.assertEqual(estimate["confidence_scope"], "support_for_provisional_behavioral_category_not_cognitive_probability")

    def test_all_concept_estimates_link_to_known_source_evidence(self):
        phase9, evidence, _ = make_bundle([1, 1, 1, 0, 1])
        state = estimate_cognitive_state(phase9, evidence)
        available = {record["evidence_id"] for record in evidence}
        for estimate in state["concept_estimates"]:
            self.assertTrue(estimate["supporting_evidence_ids"])
            self.assertTrue(set(estimate["supporting_evidence_ids"]) <= available)
        self.assertEqual(state["observed_evidence_summary"]["available_modalities"], ["interaction", "temporal_history"])
        self.assertEqual(set(state["observed_evidence_summary"]["missing_modalities"]), {"text", "audio", "visual"})

    def test_raw_text_is_not_interpreted_as_understanding(self):
        phase9, evidence, _ = make_bundle([1] * 5)
        baseline = estimate_cognitive_state(phase9, evidence)
        text = TextAdapter().from_text("u-cognitive", "I understand this concept completely", source_record_id="text-1")
        text_state = estimate_cognitive_state(phase9, [*evidence, text])
        self.assertEqual(
            baseline["concept_estimates"][0]["estimated_learning_status"],
            text_state["concept_estimates"][0]["estimated_learning_status"],
        )
        self.assertFalse(any(h["hypothesis_type"] == "possible_representation_difficulty" for h in text_state["possible_difficulty_hypotheses"]))

    def test_text_audio_visual_and_temporal_records_share_the_cognitive_interface(self):
        phase9, evidence, _ = make_bundle([1] * 5)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav_path = root / "voice.wav"
            with wave.open(str(wav_path), "wb") as audio_file:
                audio_file.setnchannels(1)
                audio_file.setsampwidth(2)
                audio_file.setframerate(8000)
                audio_file.writeframes(b"\x00\x00" * 80)
            png_path = root / "work.png"
            write_png(png_path)
            modalities = [
                TextAdapter().from_text("u-cognitive", "I used a step-by-step method.", source_record_id="text-1"),
                AudioAdapter().from_reference("u-cognitive", str(wav_path)),
                VisualAdapter().from_reference("u-cognitive", str(png_path)),
            ]
        state = estimate_cognitive_state(phase9, [*evidence, *modalities])
        self.assertEqual(set(state["observed_evidence_summary"]["available_modalities"]), {
            "interaction", "temporal_history", "text", "audio", "visual"
        })
        self.assertEqual(state["observed_evidence_summary"]["missing_modalities"], [])
        self.assertEqual(state["uncertainty"]["modality_uncertainty"], "low")
        self.assertEqual(state["uncertainty"]["inference_uncertainty"], "high")

    def test_explicit_human_annotation_can_only_create_a_low_support_hypothesis(self):
        phase9, evidence, _ = make_bundle([1] * 5)
        text = TextAdapter().from_text(
            "u-cognitive", "Here is my approach.", source_record_id="annotated-text",
            human_annotations=[{
                "annotation_type": "human",
                "hypothesis_type": "possible_representation_difficulty",
                "concept_id": "ednet_skill:7",
                "annotator_id": "reviewer-1",
                "annotation_method": "independent_manual_review",
            }],
        )
        state = estimate_cognitive_state(phase9, [*evidence, text])
        hypothesis = next(h for h in state["possible_difficulty_hypotheses"] if h["hypothesis_type"] == "possible_representation_difficulty")
        self.assertEqual(hypothesis["confidence_or_support_level"], "low")
        self.assertEqual(hypothesis["supporting_evidence_ids"], [text["evidence_id"]])

    def test_unresolved_conflict_overrides_status_and_keeps_both_sources(self):
        phase9, evidence, _ = make_bundle([1] * 5)
        text = TextAdapter().from_text("u-cognitive", "A caller-reported contradictory explanation.", source_record_id="text-conflict")
        registry = EvidenceRegistry()
        for record in [*evidence, text]:
            registry.add(record)
        interaction_record = next(record for record in evidence if record["evidence_type"] == "interaction")
        text_record = next(record for record in registry.records if record["evidence_type"] == "text")
        conflict = registry.add_conflict(
            [interaction_record["evidence_id"], text_record["evidence_id"]],
            conflict_type="caller_reported_disagreement",
            description="The two sources may disagree; no source is selected.",
        )
        state = estimate_cognitive_state(phase9, registry.records, conflicts=[conflict])
        estimate, = state["concept_estimates"]
        self.assertEqual(estimate["estimated_learning_status"], "requires_diagnostic_investigation")
        self.assertEqual(set(estimate["contradictory_evidence_ids"]), set(conflict["evidence_ids"]))
        self.assertEqual(state["observed_evidence_summary"]["contradictory_evidence_count"], 1)
        self.assertTrue(any(item["action"] == "ask_for_clarification" for item in state["diagnostic_recommendations"]))

    def test_reference_only_audio_is_counted_as_missing_modality(self):
        phase9, evidence, _ = make_bundle([1, 0])
        from mcp_ri.evidence.adapters.audio import AudioAdapter

        audio = AudioAdapter().from_reference("u-cognitive", "missing-local.wav")
        state = estimate_cognitive_state(phase9, [*evidence, audio])
        self.assertNotIn("audio", state["observed_evidence_summary"]["available_modalities"])
        self.assertIn("audio", state["observed_evidence_summary"]["missing_modalities"])
        self.assertEqual(state["uncertainty"]["modality_uncertainty"], "high")

    def test_future_sequence_event_is_rejected(self):
        phase9, evidence, _ = make_bundle([1] * 5)
        with self.assertRaisesRegex(ValueError, "after the cognitive-state sequence cutoff"):
            estimate_cognitive_state(phase9, evidence, sequence_end=3)

    def test_phase9_counts_must_match_complete_evidence_trace(self):
        phase9, evidence, _ = make_bundle([1, 0])
        with self.assertRaisesRegex(ValueError, "complete interaction evidence"):
            estimate_cognitive_state(phase9, evidence[1:])

    def test_append_only_history_links_versions_and_reports_changes(self):
        first_phase9, first_evidence, _ = make_bundle([1] * 5)
        second_phase9, second_evidence, _ = make_bundle([1] * 5 + [0] * 5)
        first = estimate_cognitive_state(first_phase9, first_evidence)
        second = estimate_cognitive_state(second_phase9, second_evidence)
        history = CognitiveStateHistory("u-cognitive")
        saved_first = history.append(first)
        saved_second = history.append(second)
        self.assertEqual(saved_first["state_version"], 1)
        self.assertEqual(saved_second["state_version"], 2)
        self.assertEqual(saved_second["previous_state_id"], saved_first["cognitive_state_id"])
        self.assertEqual(saved_second["state_change_summary"]["concept_status_changes"][0]["to_status"], "possible_difficulty")
        self.assertEqual(len(history.states), 2)
        self.assertEqual(history.states[0]["state_version"], 1)
        with self.assertRaisesRegex(ValueError, "already present"):
            history.append(second)

    def test_history_rejects_decreasing_sequence(self):
        first_phase9, first_evidence, _ = make_bundle([1] * 10)
        earlier_phase9, earlier_evidence, _ = make_bundle([1] * 5)
        history = CognitiveStateHistory("u-cognitive")
        history.append(estimate_cognitive_state(first_phase9, first_evidence))
        with self.assertRaisesRegex(ValueError, "nondecreasing"):
            history.append(estimate_cognitive_state(earlier_phase9, earlier_evidence))

    def test_recommendations_and_hypotheses_reference_known_items(self):
        phase9, evidence, _ = make_bundle([0] * 5)
        state = estimate_cognitive_state(phase9, evidence)
        validate_cognitive_state(state)
        evidence_ids = {item["evidence_id"] for item in state["evidence_references"]}
        hypothesis_ids = {item["hypothesis_id"] for item in state["possible_difficulty_hypotheses"]}
        for recommendation in state["diagnostic_recommendations"]:
            self.assertTrue(set(recommendation["supporting_evidence_ids"]) <= evidence_ids)
            self.assertTrue(set(recommendation["supporting_hypothesis_ids"]) <= hypothesis_ids)


if __name__ == "__main__":
    unittest.main()
