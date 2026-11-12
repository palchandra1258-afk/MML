"""Conservative evidence grouping and explicit modality availability."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Mapping, Sequence

from .aligner import align_records
from .evidence_schema import validate_group


EXPECTED_MODALITIES = ("text", "audio", "visual", "interaction", "temporal_history")


def _group_id(learner_id: str, session_id: str | None, evidence_ids: Sequence[str]) -> str:
    raw = json.dumps([learner_id, session_id, sorted(evidence_ids)], separators=(",", ":")).encode()
    return "eg_" + hashlib.sha256(raw).hexdigest()[:32]


def group_evidence(
    records: Sequence[Mapping[str, Any]],
    *,
    expected_modalities: Sequence[str] = EXPECTED_MODALITIES,
    alignment_tolerance_ms: int = 2000,
    alignment_candidates: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Group only same-source session records; no-session records stay singletons.

    Cross-clock timestamp proximity remains an uncertain candidate link and
    does not merge groups. Use ``align_records`` for the full candidate list.
    """
    identities = [record["evidence_id"] for record in records]
    if len(set(identities)) != len(identities):
        raise ValueError("evidence_ids must be unique before grouping")
    id_to_index = {evidence_id: index for index, evidence_id in enumerate(identities)}
    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    session_buckets: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        session = record.get("session_id")
        if session in (None, ""):
            continue
        else:
            key = (record.get("learner_id"), record.get("provenance", {}).get("source_dataset"), str(session))
            session_buckets[key].append(index)
    for members in session_buckets.values():
        for index in members[1:]:
            union(members[0], index)

    explicit_edges: set[frozenset[int]] = set()
    missing_relations: set[str] = set()
    for index, record in enumerate(records):
        for related_id in record.get("related_evidence_ids", []):
            other = id_to_index.get(related_id)
            if other is None:
                missing_relations.add(identities[index])
                continue
            if records[other].get("learner_id") != record.get("learner_id"):
                raise ValueError("explicit related-evidence links cannot cross learner IDs")
            union(index, other)
            explicit_edges.add(frozenset((index, other)))

    buckets: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records):
        buckets[find(index)].append(record)

    all_links = list(alignment_candidates) if alignment_candidates is not None else align_records(records, tolerance_ms=alignment_tolerance_ms)
    result: list[dict[str, Any]] = []
    for root, members in sorted(buckets.items(), key=lambda pair: str(pair[0])):
        learner_id = members[0]["learner_id"]
        session_ids = {member.get("session_id") for member in members}
        session_id = next(iter(session_ids)) if len(session_ids) == 1 else None
        ids = [member["evidence_id"] for member in members]
        present = sorted({member["evidence_type"] for member in members})
        modality_availability = {
            modality: {"status": "available", "reason": None}
            if modality in present
            else {"status": "unavailable", "reason": "No evidence item for this modality is present in this group."}
            for modality in expected_modalities
        }
        member_ids = set(ids)
        links = [link for link in all_links if link["left_evidence_id"] in member_ids and link["right_evidence_id"] in member_ids]
        uncertainties = sorted({flag for link in links for flag in link["uncertainty_flags"]})
        member_indices = {id_to_index[evidence_id] for evidence_id in ids}
        explicit_join = any(edge.issubset(member_indices) for edge in explicit_edges)
        shared_source_session = any(len(indices) > 1 and set(indices).issubset(member_indices)
                                    for indices in session_buckets.values())
        if explicit_join:
            basis = "explicit_evidence_relation"
        elif shared_source_session:
            basis = "source_scoped_session"
        else:
            basis = "singleton_no_shared_session"
            uncertainties.append("no_session_identifier_available")
        if any(evidence_id in missing_relations for evidence_id in ids):
            uncertainties.append("related_evidence_target_not_in_group_input")
        if basis != "singleton_no_shared_session":
            uncertainties.append("session_identifier_semantics_are_source_scoped_not_cross_dataset")
        group = {
            "schema_version": "1.0",
            "group_id": _group_id(learner_id, session_id, ids),
            "learner_id": learner_id,
            "session_id": session_id,
            "evidence_ids": sorted(ids),
            "grouping_basis": basis,
            "modalities_present": present,
            "modality_availability": modality_availability,
            "alignment_links": links,
            "uncertainty_flags": sorted(set(uncertainties)),
        }
        validate_group(group)
        result.append(group)
    return result
