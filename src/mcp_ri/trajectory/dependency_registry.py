"""Versioned concept relationships; no EdNet prerequisite edges are inferred."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .models import SCHEMA_VERSION, copy_record, stable_id
from .schemas import DEPENDENCY_SCHEMA, validate_document

RELATIONSHIP_TYPES = {"PREREQUISITE", "SUPPORTING_CONCEPT", "RELATED_CONCEPT", "ADVANCED_CONCEPT"}
VERIFICATION_STATUSES = {"verified", "manually_configured", "synthetic_test"}


class ConceptDependencyRegistry:
    """Append-only registry with explicit provenance and verification status.

    The default instance is empty. `source_concept_id` denotes the proposed
    supporting/prerequisite concept; `target_concept_id` is the concept it may
    support. Synthetic entries are excluded by production detector defaults.
    """

    def __init__(self, entries: Iterable[Mapping[str, Any]] = (), *, registry_version: int = 1,
                 created_at: str | None = None) -> None:
        self.registry_version = int(registry_version)
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self._entries: list[dict[str, Any]] = []
        for entry in entries:
            self.add(**dict(entry))

    @property
    def entries(self) -> list[dict[str, Any]]:
        return copy_record(self._entries)

    def add(self, source_concept_id: str, target_concept_id: str, relationship_type: str,
            source: str, verification_status: str, confidence: float = 0.5,
            created_at: str | None = None, dependency_id: str | None = None) -> dict[str, Any]:
        if not source_concept_id or not target_concept_id or source_concept_id == target_concept_id:
            raise ValueError("dependency endpoints must be nonempty and distinct")
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(f"unsupported relationship_type: {relationship_type}")
        if verification_status not in VERIFICATION_STATUSES:
            raise ValueError(f"unsupported verification_status: {verification_status}")
        if not source or not source.strip():
            raise ValueError("dependency source is required")
        confidence = float(confidence)
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")
        entry = {
            "dependency_id": dependency_id or stable_id("dep_", [self.registry_version, source_concept_id, target_concept_id, relationship_type, source, verification_status]),
            "source_concept_id": str(source_concept_id),
            "target_concept_id": str(target_concept_id),
            "relationship_type": relationship_type,
            "source": source.strip(),
            "verification_status": verification_status,
            "confidence": confidence,
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION,
        }
        validate_document(entry, DEPENDENCY_SCHEMA["$defs"]["dependency"], "concept dependency")
        if any(old["dependency_id"] == entry["dependency_id"] for old in self._entries):
            raise ValueError("duplicate dependency_id")
        if any(old["source_concept_id"] == entry["source_concept_id"]
               and old["target_concept_id"] == entry["target_concept_id"]
               and old["relationship_type"] == entry["relationship_type"] for old in self._entries):
            raise ValueError("duplicate concept relationship")
        if relationship_type == "PREREQUISITE":
            graph: dict[str, set[str]] = {}
            for old in self._entries:
                if old["relationship_type"] == "PREREQUISITE":
                    graph.setdefault(old["source_concept_id"], set()).add(old["target_concept_id"])
            pending = [str(target_concept_id)]
            visited: set[str] = set()
            while pending:
                node = pending.pop()
                if node == source_concept_id:
                    raise ValueError("prerequisite relationship would create a dependency cycle")
                if node not in visited:
                    visited.add(node)
                    pending.extend(graph.get(node, ()))
        self._entries.append(entry)
        return copy_record(entry)

    def supporting_concepts(self, target_concept_id: str, *, allow_synthetic: bool = False) -> list[dict[str, Any]]:
        return [copy_record(item) for item in self._entries
                if item["target_concept_id"] == target_concept_id
                and item["relationship_type"] in {"PREREQUISITE", "SUPPORTING_CONCEPT"}
                and (allow_synthetic or item["verification_status"] != "synthetic_test")]

    def as_dict(self) -> dict[str, Any]:
        document = {
            "schema_version": SCHEMA_VERSION,
            "registry_version": self.registry_version,
            "created_at": self.created_at,
            "dependencies": self.entries,
        }
        validate_document(document, DEPENDENCY_SCHEMA, "dependency registry")
        return document
