"""Canonical evidence-record construction and normalization."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from .evidence_schema import validate_evidence


PROCESSING_VERSION = "mcp-ri-evidence-1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_evidence_id(
    evidence_type: str,
    learner_id: str,
    source_dataset: str,
    source_record_id: str | None,
    content_fingerprint: str,
    session_id: str | None,
    event_timestamp: str | None,
) -> str:
    identity = {
        "evidence_type": evidence_type,
        "learner_id": learner_id,
        "source_dataset": source_dataset,
        "source_record_id": source_record_id,
        "session_id": session_id,
        "event_timestamp": event_timestamp,
        "content_fingerprint": content_fingerprint if source_record_id is None else None,
    }
    return "ev_" + _canonical_hash(identity)[:32]


def normalize_evidence(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Fill stable IDs/fingerprints and validate an adapter-produced record.

    Event time is never synthesized. Ingestion and processing times are actual
    normalization times and remain separate from the source event timestamp.
    """
    record = json.loads(json.dumps(dict(draft), ensure_ascii=False, default=str))
    record.setdefault("schema_version", "1.0")
    record.setdefault("related_evidence_ids", [])
    record.setdefault("duplicate_candidates", [])
    record.setdefault("content", {})
    record.setdefault("uncertainty", {"flags": [], "processing_confidence": None, "notes": []})
    record.setdefault("processing", {})
    record["processing"].setdefault("processing_timestamp", utc_now())
    record["processing"].setdefault("quality_flags", [])
    record["processing"].setdefault("missing_fields", [])
    record["processing"].setdefault("transformation_history", [])
    record["temporal"].setdefault("ingestion_timestamp", utc_now())
    record["temporal"].setdefault("sequence_number", None)
    record["temporal"].setdefault("event_timestamp", None)
    record["temporal"].setdefault("temporal_precision", "not_available")
    record["temporal"].setdefault("timestamp_source", None)
    record["content_fingerprint"] = _canonical_hash(record["content"])
    record.setdefault("evidence_id", stable_evidence_id(
        record["evidence_type"], record["learner_id"], record["provenance"]["source_dataset"],
        record["provenance"].get("source_record_id"), record["content_fingerprint"],
        record.get("session_id"), record["temporal"].get("event_timestamp"),
    ))
    validate_evidence(record)
    return record


def base_record(
    *,
    learner_id: str,
    session_id: str | None,
    evidence_type: str,
    event_timestamp: str | None,
    sequence_number: int | None,
    temporal_precision: str,
    timestamp_source: str | None,
    source_dataset: str,
    source_file: str | None,
    source_record_id: str | None,
    source_modality: str,
    processing_method: str,
    content: Mapping[str, Any],
    status: str = "processed",
    extraction_method: str = "metadata_only",
    quality_flags: list[str] | None = None,
    missing_fields: list[str] | None = None,
    transformation_history: list[str] | None = None,
    uncertainty_flags: list[str] | None = None,
    uncertainty_notes: list[str] | None = None,
) -> dict[str, Any]:
    if learner_id is None or not str(learner_id).strip():
        raise ValueError("learner_id is required")
    now = utc_now()
    draft = {
        "schema_version": "1.0",
        "learner_id": str(learner_id),
        "session_id": str(session_id) if session_id not in (None, "") else None,
        "evidence_type": evidence_type,
        "temporal": {
            "event_timestamp": event_timestamp,
            "ingestion_timestamp": now,
            "sequence_number": sequence_number,
            "temporal_precision": temporal_precision,
            "timestamp_source": timestamp_source,
        },
        "provenance": {
            "source_dataset": source_dataset,
            "source_file": source_file,
            "source_record_id": source_record_id,
            "source_modality": source_modality,
            "processing_method": processing_method,
            "processing_version": PROCESSING_VERSION,
        },
        "content": dict(content),
        "processing": {
            "status": status,
            "processing_timestamp": now,
            "extraction_method": extraction_method,
            "quality_flags": list(quality_flags or []),
            "missing_fields": list(missing_fields or []),
            "transformation_history": list(transformation_history or []),
        },
        "uncertainty": {
            "flags": list(uncertainty_flags or []),
            "processing_confidence": None,
            "notes": list(uncertainty_notes or []),
        },
        "related_evidence_ids": [],
        "duplicate_candidates": [],
    }
    return normalize_evidence(draft)
