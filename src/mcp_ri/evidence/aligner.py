"""Conservative timestamp/session alignment candidate generation."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .evidence_schema import validate_alignment


def _event_ms(record: Mapping[str, Any]) -> int | None:
    temporal = record.get("temporal", {})
    if temporal.get("temporal_precision") != "millisecond":
        return None
    value = temporal.get("event_timestamp")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def align_records(records: Sequence[Mapping[str, Any]], tolerance_ms: int = 2000) -> list[dict[str, Any]]:
    """Return candidate links without force-merging cross-source observations.

    Dataset-scoped session IDs and caller-supplied related IDs are stronger
    links. Close timestamps across independent clock sources are candidates
    with high alignment uncertainty, never asserted synchronization.
    """
    if tolerance_ms < 0:
        raise ValueError("tolerance_ms must be nonnegative")
    links: list[dict[str, Any]] = []
    by_id = {record["evidence_id"]: record for record in records}
    for index, left in enumerate(records):
        left_id = left["evidence_id"]
        related = set(left.get("related_evidence_ids", []))
        for right in records[index + 1:]:
            right_id = right["evidence_id"]
            right_related = set(right.get("related_evidence_ids", []))
            if left_id in right_related or right_id in related:
                if left.get("learner_id") != right.get("learner_id"):
                    raise ValueError("explicit evidence alignment cannot cross learner IDs")
                links.append(_link(left, right, "explicit_related", None, "low", []))
                continue
            left_session = left.get("session_id")
            right_session = right.get("session_id")
            same_source = left.get("provenance", {}).get("source_dataset") == right.get("provenance", {}).get("source_dataset")
            same_learner = left.get("learner_id") == right.get("learner_id")
            if same_learner and same_source and left_session not in (None, "") and left_session == right_session:
                left_time, right_time = _event_ms(left), _event_ms(right)
                delta = abs(left_time - right_time) if left_time is not None and right_time is not None else None
                flags = []
                status = "same_source_session"
                uncertainty = "unknown" if delta is None else "low" if delta <= tolerance_ms else "high"
                if delta is None:
                    flags.append("event_timestamp_missing_or_non_numeric")
                elif delta > tolerance_ms:
                    flags.append("same_session_events_exceed_alignment_tolerance")
                links.append(_link(left, right, status, delta, uncertainty, flags))
                continue
            if not same_learner:
                continue
            left_time, right_time = _event_ms(left), _event_ms(right)
            if left_time is None or right_time is None:
                continue
            delta = abs(left_time - right_time)
            if delta > tolerance_ms:
                continue
            left_clock = left.get("temporal", {}).get("timestamp_source")
            right_clock = right.get("temporal", {}).get("timestamp_source")
            if left_clock and left_clock == right_clock:
                links.append(_link(left, right, "approximate_timestamp_candidate", delta, "medium", ["same_clock_source_but_no_shared_session_key"]))
            else:
                links.append(_link(left, right, "uncertain_cross_source_candidate", delta, "high", ["cross_source_clock_offset_unverified"]))
    for link in links:
        validate_alignment(link)
    return links


def _link(left: Mapping[str, Any], right: Mapping[str, Any], kind: str, delta: int | None, uncertainty: str, flags: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "left_evidence_id": left["evidence_id"],
        "right_evidence_id": right["evidence_id"],
        "alignment_type": kind,
        "absolute_delta_ms": delta,
        "alignment_uncertainty": uncertainty,
        "uncertainty_flags": flags,
    }
