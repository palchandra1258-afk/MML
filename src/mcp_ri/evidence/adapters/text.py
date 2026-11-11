"""Text adapter: preserve authored text and record transparent normalization only."""

from __future__ import annotations

import unicodedata
from typing import Any, Mapping, Sequence

from ..normalizer import base_record


class TextAdapter:
    def from_text(
        self,
        learner_id: str,
        text: str,
        *,
        source_dataset: str = "caller-provided",
        source_file: str | None = None,
        source_record_id: str | None = None,
        session_id: str | None = None,
        event_timestamp: str | None = None,
        timestamp_source: str | None = None,
        temporal_precision: str | None = None,
        sequence_number: int | None = None,
        language: str | None = None,
        human_annotations: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        normalized = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n")).strip()
        return base_record(
            learner_id=learner_id,
            session_id=session_id,
            evidence_type="text",
            event_timestamp=event_timestamp,
            sequence_number=sequence_number,
            temporal_precision=temporal_precision or ("unknown" if event_timestamp else "not_available"),
            timestamp_source=timestamp_source,
            source_dataset=source_dataset,
            source_file=source_file,
            source_record_id=source_record_id,
            source_modality="text",
            processing_method="unicode_nfc_and_line_ending_normalization",
            content={
                "raw_text": text,
                "normalized_text": normalized,
                "language": language,
                "human_annotations": [dict(item) for item in human_annotations],
                "tokenization": {"method": "whitespace_split", "token_count": len(normalized.split())},
            },
            extraction_method="caller_supplied_text",
            missing_fields=[name for name, value in (("language", language), ("event_timestamp", event_timestamp)) if value is None],
            transformation_history=["line endings normalized", "Unicode NFC applied", "outer whitespace trimmed"],
            uncertainty_notes=["Text normalization does not establish the truth or meaning of the authored text."],
        )
