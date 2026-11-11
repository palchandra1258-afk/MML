"""Visual artifact reference adapter with image metadata/hash extraction."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlparse

from ..normalizer import base_record


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _local_path(reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if parsed.scheme:
        return None
    return Path(reference)


def _image_metadata(path: Path) -> tuple[str | None, int | None, int | None, str | None]:
    with path.open("rb") as stream:
        header = stream.read(32)
    if header.startswith(PNG_SIGNATURE) and len(header) >= 24 and header[12:16] == b"IHDR":
        width, height = struct.unpack(">II", header[16:24])
        return "png", width, height, "image/png"
    if header[:3] == b"\xff\xd8\xff":
        width, height = _jpeg_dimensions(path)
        return "jpeg", width, height, "image/jpeg"
    return path.suffix.lower().lstrip(".") or None, None, None, None


def _jpeg_dimensions(path: Path) -> tuple[int | None, int | None]:
    frame_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    with path.open("rb") as stream:
        if stream.read(2) != b"\xff\xd8":
            return None, None
        while True:
            byte = stream.read(1)
            if not byte:
                return None, None
            if byte != b"\xff":
                continue
            marker = stream.read(1)
            while marker == b"\xff":
                marker = stream.read(1)
            if not marker:
                return None, None
            code = marker[0]
            if code in {0xD8, 0xD9, 0x01} or 0xD0 <= code <= 0xD7:
                if code == 0xD9:
                    return None, None
                continue
            length_bytes = stream.read(2)
            if len(length_bytes) != 2:
                return None, None
            length = struct.unpack(">H", length_bytes)[0]
            if length < 2:
                return None, None
            if code in frame_markers:
                frame = stream.read(min(length - 2, 5))
                if len(frame) < 5:
                    return None, None
                height, width = struct.unpack(">HH", frame[1:5])
                return width, height
            stream.seek(length - 2, 1)


class VisualAdapter:
    def from_reference(
        self,
        learner_id: str,
        visual_reference: str,
        *,
        source_dataset: str = "caller-provided",
        source_record_id: str | None = None,
        source_file: str | None = None,
        session_id: str | None = None,
        event_timestamp: str | None = None,
        timestamp_source: str | None = None,
        temporal_precision: str | None = None,
        sequence_number: int | None = None,
        ocr_text: str | None = None,
        ocr_provenance: str | None = None,
        ocr_error: str | None = None,
        metadata: dict[str, Any] | None = None,
        human_annotations: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        if not visual_reference:
            raise ValueError("visual_reference is required")
        if ocr_text is not None and ocr_error:
            raise ValueError("OCR text and ocr_error cannot both be supplied")
        local = _local_path(visual_reference)
        available = bool(local and local.is_file())
        fmt = width = height = mime = digest = size = None
        if available and local is not None:
            fmt, width, height, mime = _image_metadata(local)
            size = local.stat().st_size
            hasher = hashlib.sha256()
            with local.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
        supplied = metadata or {}
        fmt = supplied.get("format", fmt)
        width = supplied.get("width", width)
        height = supplied.get("height", height)
        mime = supplied.get("mime_type", mime)
        image_metadata_incomplete = bool(available and (width is None or height is None or mime is None))
        status = "available" if ocr_text is not None else "failed" if ocr_error else "pending"
        flags = [] if available else ["visual_asset_not_available_for_inspection"]
        if image_metadata_incomplete:
            flags.append("image_metadata_incomplete")
        missing = [key for key, value in (("width", width), ("height", height), ("mime_type", mime)) if value is None]
        if ocr_text is None:
            missing.append("ocr_text")
        elif ocr_provenance is None:
            missing.append("ocr_provenance")
        return base_record(
            learner_id=learner_id,
            session_id=session_id,
            evidence_type="visual",
            event_timestamp=event_timestamp,
            sequence_number=sequence_number,
            temporal_precision=temporal_precision or ("unknown" if event_timestamp else "not_available"),
            timestamp_source=timestamp_source,
            source_dataset=source_dataset,
            source_file=source_file,
            source_record_id=source_record_id,
            source_modality="visual",
            processing_method="reference_preservation_and_stdlib_image_header_metadata",
            content={
                "visual_reference": visual_reference,
                "format": fmt,
                "mime_type": mime,
                "width": width,
                "height": height,
                "size_bytes": size,
                "sha256": digest,
                "ocr_text": ocr_text,
                "ocr_status": status,
                "ocr_provenance": ocr_provenance,
                "ocr_error": ocr_error,
                "human_annotations": [dict(item) for item in human_annotations],
            },
            status="partial" if available and (ocr_error or image_metadata_incomplete) else "processed" if available else "reference_only",
            extraction_method="sha256_and_image_header" if available else "reference_metadata_only",
            quality_flags=flags + (["ocr_extraction_failed"] if ocr_error else []),
            missing_fields=missing,
            transformation_history=["binary payload not embedded in evidence JSON"],
            uncertainty_flags=(
                (["ocr_pending"] if status == "pending" else ["ocr_extraction_failed"] if ocr_error else [])
                + (["image_metadata_incomplete"] if image_metadata_incomplete else [])
            ),
            uncertainty_notes=(
                (["No OCR or visual interpretation is run by this adapter."] if status == "pending" else [ocr_error] if ocr_error else [])
                + (["Image header metadata is incomplete or could not be parsed."] if image_metadata_incomplete else [])
            ),
        )
