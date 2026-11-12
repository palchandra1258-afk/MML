"""Adapter for already-processed EdNet KT1 interaction rows."""

from __future__ import annotations

from typing import Any, Mapping

from ...ednet_preprocessing import parse_skill_tags
from ..normalizer import base_record


class InteractionAdapter:
    source_dataset = "EdNet-KT1"

    def from_processed_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        learner_raw = row.get("learner_id")
        learner_id = "" if learner_raw is None else str(learner_raw).strip()
        if not learner_id:
            raise ValueError("processed EdNet row is missing learner_id")
        raw_timestamp_value = row.get("timestamp")
        raw_timestamp = "" if raw_timestamp_value is None else str(raw_timestamp_value).strip()
        event_timestamp = raw_timestamp or None
        source_order_raw = row.get("source_row_order")
        sequence_number = int(source_order_raw) if source_order_raw not in (None, "") else None
        session = row.get("session_id")
        qid_raw = row.get("question_id")
        qid = ("" if qid_raw is None else str(qid_raw).strip()) or None
        correctness_raw = row.get("correctness")
        correctness = int(correctness_raw) if str(correctness_raw).strip() in {"0", "1"} else None
        tags = list(dict.fromkeys(
            f"ednet_skill:{tag}"
            for tag in parse_skill_tags(row.get("skill_tags", row.get("current_skill_tags", "")))
        ))
        missing = []
        if event_timestamp is None:
            missing.append("timestamp")
        if qid is None:
            missing.append("question_id")
        if not tags:
            missing.append("skill_tags")
        if correctness is None:
            missing.append("correctness")
        timestamp_numeric = event_timestamp is not None and event_timestamp.isdigit()
        source_file = f"data/raw/ednet/ednet-kt1.zip#KT1/{learner_id}.csv"
        return base_record(
            learner_id=learner_id,
            session_id=session,
            evidence_type="interaction",
            event_timestamp=event_timestamp,
            sequence_number=sequence_number,
            temporal_precision="millisecond" if timestamp_numeric else "not_available" if event_timestamp is None else "unknown",
            timestamp_source="EdNet KT1 shifted question-given timestamp" if event_timestamp else None,
            source_dataset=self.source_dataset,
            source_file=source_file,
            source_record_id=f"{learner_id}:{sequence_number}" if sequence_number is not None else None,
            source_modality="interaction",
            processing_method="reuse_processed_ednet_row_and_existing_skill_tag_parser",
            content={
                "question_id": qid,
                "solving_id": ("" if row.get("solving_id") is None else str(row.get("solving_id")).strip()) or None,
                "submitted_answer": ("" if row.get("submitted_answer") is None else str(row.get("submitted_answer")).strip()) or None,
                "correctness": correctness,
                "skill_ids": tags,
                "is_exact_duplicate": str(row.get("is_exact_duplicate", "0")) == "1",
            },
            extraction_method="processed_csv_field_mapping",
            missing_fields=missing,
            transformation_history=["preserved source timestamp text", "skill tags parsed and deduplicated"],
            uncertainty_flags=["correctness_is_behavioral_outcome_not_cognitive_label"],
            uncertainty_notes=["Absolute EdNet timestamps are publisher-shifted; source order is retained."],
        )
