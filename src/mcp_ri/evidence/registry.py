"""Small in-memory registry preserving duplicate candidates and conflicts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .evidence_schema import validate_conflict, validate_evidence


class EvidenceRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, dict[str, Any]] = {}
        self._by_fingerprint: dict[str, list[str]] = {}
        self.conflicts: list[dict[str, Any]] = []

    @property
    def records(self) -> list[dict[str, Any]]:
        return list(self._by_id.values())

    def add(self, record: Mapping[str, Any]) -> dict[str, Any]:
        validate_evidence(record)
        candidate = json.loads(json.dumps(dict(record), ensure_ascii=False))
        evidence_id = candidate["evidence_id"]
        if evidence_id in self._by_id:
            return {"status": "duplicate_reingestion", "evidence_id": evidence_id, "duplicate_of": evidence_id}
        fingerprint = candidate["content_fingerprint"]
        possible = [existing_id for existing_id in self._by_fingerprint.get(fingerprint, [])
                    if self._by_id[existing_id]["learner_id"] == candidate["learner_id"]
                    and existing_id != evidence_id]
        candidate["duplicate_candidates"] = sorted(set(candidate.get("duplicate_candidates", [])) | set(possible))
        if possible:
            candidate["uncertainty"]["flags"] = sorted(set(candidate["uncertainty"]["flags"] + ["possible_duplicate_content_retained"]))
            for existing_id in possible:
                existing = self._by_id[existing_id]
                existing["duplicate_candidates"] = sorted(set(existing.get("duplicate_candidates", [])) | {evidence_id})
                existing["uncertainty"]["flags"] = sorted(set(existing["uncertainty"]["flags"] + ["possible_duplicate_content_retained"]))
                validate_evidence(existing)
        validate_evidence(candidate)
        self._by_id[evidence_id] = candidate
        self._by_fingerprint.setdefault(fingerprint, []).append(evidence_id)
        return {"status": "possible_content_duplicate_retained" if possible else "added", "evidence_id": evidence_id, "duplicate_candidates": candidate["duplicate_candidates"]}

    def add_conflict(
        self,
        evidence_ids: list[str],
        *,
        conflict_type: str,
        description: str,
        resolution_status: str = "unresolved",
    ) -> dict[str, Any]:
        if len(set(evidence_ids)) < 2:
            raise ValueError("a conflict requires at least two distinct evidence records")
        unknown = sorted(set(evidence_ids) - set(self._by_id))
        if unknown:
            raise ValueError(f"conflict refers to unknown evidence IDs: {unknown}")
        ordered_ids = sorted(set(evidence_ids))
        records = [self._by_id[item] for item in ordered_ids]
        timestamps = [item["temporal"]["event_timestamp"] for item in records]
        conflict = {
            "schema_version": "1.0",
            "conflict_id": "ec_" + hashlib.sha256("|".join(ordered_ids).encode()).hexdigest()[:32],
            "evidence_ids": ordered_ids,
            "conflict_type": conflict_type,
            "source_modalities": sorted({item["provenance"]["source_modality"] for item in records}),
            "timestamp_relationship": "same_event_time" if timestamps[0] is not None and len(set(timestamps)) == 1 else "different_or_missing_event_times",
            "event_timestamps": timestamps,
            "description": description,
            "resolution_status": resolution_status,
            "resolution": None,
            "cognitive_interpretation": None,
        }
        validate_conflict(conflict)
        self.conflicts.append(conflict)
        return conflict
