"""Audio-reference adapter with WAV metadata support and no automatic ASR."""

from __future__ import annotations

import hashlib
import wave
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlparse

from ..normalizer import base_record


def _local_path(reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if parsed.scheme:
        return None
    return Path(reference)


class AudioAdapter:
    def from_reference(
        self,
        learner_id: str,
        audio_reference: str,
        *,
        source_dataset: str = "caller-provided",
        source_record_id: str | None = None,
        source_file: str | None = None,
        session_id: str | None = None,
        event_timestamp: str | None = None,
        timestamp_source: str | None = None,
        temporal_precision: str | None = None,
        sequence_number: int | None = None,
        language: str | None = None,
        transcription: str | None = None,
        transcription_provenance: str | None = None,
        transcription_error: str | None = None,
        metadata: dict[str, Any] | None = None,
        human_annotations: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        if not audio_reference:
            raise ValueError("audio_reference is required")
        if transcription is not None and transcription_error:
            raise ValueError("transcription text and transcription_error cannot both be supplied")
        local = _local_path(audio_reference)
        available = bool(local and local.is_file())
        digest = None
        size = None
        audio_format = (local.suffix.lower().lstrip(".") if local else Path(urlparse(audio_reference).path).suffix.lower().lstrip(".")) or None
        sample_rate = None
        channels = None
        duration = None
        wav_metadata_failed = False
        if available and local is not None:
            hasher = hashlib.sha256()
            with local.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
            size = local.stat().st_size
            if audio_format == "wav":
                try:
                    with wave.open(str(local), "rb") as source:
                        sample_rate = source.getframerate()
                        channels = source.getnchannels()
                        duration = source.getnframes() / sample_rate if sample_rate else None
                except (wave.Error, EOFError):
                    audio_format = "wav"
                    wav_metadata_failed = True
        supplied = metadata or {}
        audio_format = supplied.get("format", audio_format)
        duration = supplied.get("duration_seconds", duration)
        sample_rate = supplied.get("sample_rate_hz", sample_rate)
        channels = supplied.get("channels", channels)
        audio_metadata_incomplete = bool(available and (duration is None or sample_rate is None))
        transcript_status = "available" if transcription is not None else "failed" if transcription_error else "pending"
        flags = [] if available else ["audio_asset_not_available_for_inspection"]
        missing = [key for key, value in (("duration_seconds", duration), ("sample_rate_hz", sample_rate), ("language", language)) if value is None]
        if transcription is None:
            missing.append("transcription")
        elif transcription_provenance is None:
            missing.append("transcription_provenance")
        if wav_metadata_failed:
            flags.append("wav_metadata_extraction_failed")
        if audio_metadata_incomplete:
            flags.append("audio_metadata_incomplete")
        return base_record(
            learner_id=learner_id,
            session_id=session_id,
            evidence_type="audio",
            event_timestamp=event_timestamp,
            sequence_number=sequence_number,
            temporal_precision=temporal_precision or ("unknown" if event_timestamp else "not_available"),
            timestamp_source=timestamp_source,
            source_dataset=source_dataset,
            source_file=source_file,
            source_record_id=source_record_id,
            source_modality="audio",
            processing_method="reference_preservation_and_optional_stdlib_wav_metadata",
            content={
                "audio_reference": audio_reference,
                "format": audio_format,
                "size_bytes": size,
                "sha256": digest,
                "duration_seconds": duration,
                "sample_rate_hz": sample_rate,
                "channels": channels,
                "language": language,
                "transcription": transcription,
                "transcription_status": transcript_status,
                "transcription_provenance": transcription_provenance,
                "transcription_error": transcription_error,
                "human_annotations": [dict(item) for item in human_annotations],
            },
            status="partial" if available and (transcription_error or wav_metadata_failed or audio_metadata_incomplete) else "processed" if available else "reference_only",
            extraction_method="sha256_and_wave_module" if available else "reference_metadata_only",
            quality_flags=flags + (["transcription_extraction_failed"] if transcription_error else []),
            missing_fields=missing,
            transformation_history=["binary payload not embedded in evidence JSON"],
            uncertainty_flags=(
                (["transcription_pending"] if transcript_status == "pending" else ["transcription_extraction_failed"] if transcription_error else [])
                + (["wav_metadata_extraction_failed"] if wav_metadata_failed else [])
                + (["audio_metadata_incomplete"] if audio_metadata_incomplete else [])
            ),
            uncertainty_notes=(
                (["No speech recognition is run by this adapter."] if transcript_status == "pending" else [transcription_error] if transcription_error else [])
                + (["WAV metadata could not be read from the local asset."] if wav_metadata_failed else [])
                + (["Audio duration or sample-rate metadata is unavailable."] if audio_metadata_incomplete else [])
            ),
        )
