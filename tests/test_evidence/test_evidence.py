from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import wave
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.evidence.adapters.audio import AudioAdapter  # noqa: E402
from mcp_ri.evidence.adapters.interaction import InteractionAdapter  # noqa: E402
from mcp_ri.evidence.adapters.temporal import TemporalHistoryAdapter  # noqa: E402
from mcp_ri.evidence.adapters.text import TextAdapter  # noqa: E402
from mcp_ri.evidence.adapters.visual import VisualAdapter  # noqa: E402
from mcp_ri.evidence.aligner import align_records  # noqa: E402
from mcp_ri.evidence.evidence_schema import validate_alignment, validate_conflict, validate_evidence  # noqa: E402
from mcp_ri.evidence.grouping import group_evidence  # noqa: E402
from mcp_ri.evidence.registry import EvidenceRegistry  # noqa: E402
from mcp_ri.evidence.state_bridge import apply_interaction_evidence  # noqa: E402
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402


def interaction_row(order: int, *, learner: str = "u-test", timestamp: int | None = None,
                    session: str | None = None, correctness: str = "1") -> dict[str, str]:
    return {
        "learner_id": learner,
        "source_row_order": str(order),
        "timestamp": str(timestamp if timestamp is not None else 1000 + order),
        "question_id": f"q{order + 1}",
        "solving_id": f"solve-{order}",
        "submitted_answer": "b",
        "correctness": correctness,
        "skill_tags": "7;8;7",
        "session_id": session or "",
        "is_exact_duplicate": "0",
    }


def make_png(path: Path, width: int = 2, height: int = 3) -> None:
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    raw = b"\x00" + (b"\x00\x00\x00" * width)
    image = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw * height))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(image)


class EvidenceTests(unittest.TestCase):
    def test_normalizer_schema_and_stable_source_identity(self):
        adapter = InteractionAdapter()
        row = interaction_row(4)
        first = adapter.from_processed_row(row)
        again = adapter.from_processed_row(row)
        validate_evidence(first)
        self.assertEqual(first["evidence_id"], again["evidence_id"])
        self.assertEqual(first["temporal"]["event_timestamp"], row["timestamp"])
        self.assertNotEqual(first["temporal"]["event_timestamp"], first["temporal"]["ingestion_timestamp"])
        self.assertEqual(first["provenance"]["source_record_id"], "u-test:4")
        self.assertEqual(first["content"]["skill_ids"], ["ednet_skill:7", "ednet_skill:8"])
        self.assertEqual(first["session_id"], None)
        self.assertEqual(first["content"]["solving_id"], "solve-4")

    def test_invalid_evidence_rejected(self):
        record = InteractionAdapter().from_processed_row(interaction_row(0))
        record["schema_version"] = "99"
        with self.assertRaises(ValueError):
            validate_evidence(record)

    def test_text_normalization_preserves_raw_text_without_interpretation(self):
        record = TextAdapter().from_text("u-text", " Cafe\u0301\r\nmath ", language="en")
        self.assertEqual(record["content"]["raw_text"], " Cafe\u0301\r\nmath ")
        self.assertEqual(record["content"]["normalized_text"], "Café\nmath")
        self.assertEqual(record["content"]["tokenization"]["token_count"], 2)
        self.assertIsNone(record["uncertainty"]["processing_confidence"])

    def test_audio_wav_metadata_and_pending_transcription(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.wav"
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b"\x00\x00" * 800)
            record = AudioAdapter().from_reference("u-audio", str(path))
        self.assertEqual(record["content"]["format"], "wav")
        self.assertEqual(record["content"]["sample_rate_hz"], 8000)
        self.assertEqual(record["content"]["duration_seconds"], 0.1)
        self.assertEqual(record["content"]["transcription_status"], "pending")
        self.assertEqual(len(record["content"]["sha256"]), 64)

    def test_audio_failed_transcription_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.wav"
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b"\x00\x00" * 80)
            record = AudioAdapter().from_reference("u-audio", str(path), transcription_error="decoder unavailable")
        self.assertEqual(record["processing"]["status"], "partial")
        self.assertEqual(record["content"]["transcription_status"], "failed")
        self.assertIn("transcription_extraction_failed", record["processing"]["quality_flags"])

    def test_audio_invalid_wav_is_partial_not_silent_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.wav"
            path.write_bytes(b"not a wave file")
            record = AudioAdapter().from_reference("u-audio", str(path))
        self.assertEqual(record["processing"]["status"], "partial")
        self.assertIn("wav_metadata_extraction_failed", record["processing"]["quality_flags"])

    def test_visual_png_metadata_hash_and_pending_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "work.png"
            make_png(path)
            record = VisualAdapter().from_reference("u-visual", str(path))
        self.assertEqual(record["content"]["format"], "png")
        self.assertEqual((record["content"]["width"], record["content"]["height"]), (2, 3))
        self.assertEqual(record["content"]["ocr_status"], "pending")
        self.assertEqual(len(record["content"]["sha256"]), 64)

    def test_visual_ocr_failure_keeps_asset_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "work.png"
            make_png(path)
            record = VisualAdapter().from_reference("u-visual", str(path), ocr_error="synthetic OCR failure")
        self.assertEqual(record["processing"]["status"], "partial")
        self.assertEqual(record["content"]["ocr_status"], "failed")
        self.assertEqual(record["content"]["visual_reference"], str(path))

    def test_unreadable_visual_header_is_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.png"
            path.write_bytes(b"not a png")
            record = VisualAdapter().from_reference("u-visual", str(path))
        self.assertEqual(record["processing"]["status"], "partial")
        self.assertIn("image_metadata_incomplete", record["processing"]["quality_flags"])

    def test_missing_modalities_remain_explicit_and_group_is_valid(self):
        record = InteractionAdapter().from_processed_row(interaction_row(0))
        group, = group_evidence([record])
        self.assertIn("interaction", group["modalities_present"])
        for modality in ("text", "audio", "visual"):
            self.assertEqual(group["modality_availability"][modality]["status"], "unavailable")
        self.assertEqual(group["grouping_basis"], "singleton_no_shared_session")

    def test_timestamp_candidate_does_not_force_cross_source_merge(self):
        interaction = InteractionAdapter().from_processed_row(interaction_row(0, timestamp=5000))
        text = TextAdapter().from_text("u-test", "work", event_timestamp="5000", timestamp_source="device-clock", temporal_precision="millisecond")
        links = align_records([interaction, text])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["alignment_type"], "uncertain_cross_source_candidate")
        self.assertEqual(links[0]["alignment_uncertainty"], "high")
        groups = group_evidence([interaction, text])
        self.assertEqual(len(groups), 2)
        validate_alignment(links[0])

    def test_unknown_timestamp_precision_does_not_make_candidate(self):
        interaction = InteractionAdapter().from_processed_row(interaction_row(0, timestamp=5000))
        text = TextAdapter().from_text("u-test", "work", event_timestamp="5000", timestamp_source="device-clock")
        self.assertEqual(align_records([interaction, text]), [])

    def test_same_source_session_groups_events(self):
        adapter = InteractionAdapter()
        records = [adapter.from_processed_row(interaction_row(i, session="sess-1")) for i in (0, 1)]
        groups = group_evidence(records)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["grouping_basis"], "source_scoped_session")

    def test_explicit_relation_groups_same_learner_records(self):
        adapter = InteractionAdapter()
        left = adapter.from_processed_row(interaction_row(0))
        right = adapter.from_processed_row(interaction_row(1))
        right["related_evidence_ids"] = [left["evidence_id"]]
        validate_evidence(right)
        groups = group_evidence([left, right])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["grouping_basis"], "explicit_evidence_relation")

    def test_explicit_relation_cannot_cross_learners(self):
        left = InteractionAdapter().from_processed_row(interaction_row(0, learner="u-one"))
        right = TextAdapter().from_text("u-two", "separate learner", source_record_id="text-two")
        right["related_evidence_ids"] = [left["evidence_id"]]
        validate_evidence(right)
        with self.assertRaises(ValueError):
            group_evidence([left, right])

    def test_possible_duplicates_are_retained_and_linked_both_ways(self):
        adapter = TextAdapter()
        registry = EvidenceRegistry()
        first = registry.add(adapter.from_text("u-text", "same content", source_record_id="text-a"))
        second = registry.add(adapter.from_text("u-text", "same content", source_record_id="text-b"))
        self.assertEqual(len(registry.records), 2)
        self.assertEqual(registry.records[0]["duplicate_candidates"], [second["evidence_id"]])
        self.assertEqual(registry.records[1]["duplicate_candidates"], [first["evidence_id"]])

    def test_conflict_preserves_both_records_and_unresolved_status(self):
        adapter = InteractionAdapter()
        registry = EvidenceRegistry()
        observed = registry.add(adapter.from_processed_row(interaction_row(0, correctness="1")))
        explanation = registry.add(TextAdapter().from_text("u-test", "my synthetic explanation", source_record_id="text-1"))
        conflict = registry.add_conflict(
            [observed["evidence_id"], explanation["evidence_id"]],
            conflict_type="synthetic_interaction_text_disagreement",
            description="A synthetic correct interaction and caller-reported inconsistent explanation are retained without selecting a source.",
        )
        validate_conflict(conflict)
        self.assertEqual(conflict["resolution_status"], "unresolved")
        self.assertEqual(conflict["source_modalities"], ["interaction", "text"])
        self.assertIsNone(conflict["cognitive_interpretation"])
        self.assertEqual(len(registry.records), 2)

    def test_phase9_integration_updates_state_from_normalized_event(self):
        adapter = InteractionAdapter()
        first = adapter.from_processed_row(interaction_row(0, correctness="0"))
        new_event = adapter.from_processed_row(interaction_row(1, timestamp=1001, correctness="1"))
        state = LearnerStateAccumulator("u-test")
        before = apply_interaction_evidence(state, first)
        after = apply_interaction_evidence(state, new_event)
        self.assertEqual(before["observation_summary"]["total_interactions"], 1)
        self.assertEqual(after["observation_summary"]["total_interactions"], 2)
        self.assertEqual(after["learning_performance"]["attempts"], 2)
        self.assertEqual(after["learning_performance"]["correct"], 1)
        self.assertEqual(new_event["temporal"]["event_timestamp"], "1001")
        self.assertIn("EdNet-KT1", new_event["provenance"]["source_dataset"])
        temporal = TemporalHistoryAdapter().from_learner_state(
            after, state_reference="synthetic-test-state", related_evidence_ids=[first["evidence_id"], new_event["evidence_id"]]
        )
        self.assertEqual(temporal["related_evidence_ids"], sorted([first["evidence_id"], new_event["evidence_id"]]))


if __name__ == "__main__":
    unittest.main()
