"""Explicit registry of representation-delivery capabilities."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from .representation_taxonomy import REPRESENTATION_IDS, TAXONOMY_VERSION


VALID_STATUSES = {"available", "planned", "unavailable"}


class RepresentationAvailabilityRegistry:
    """Track which representation types have a real provider/content source.

    Default entries are deliberately non-executable. A capability becomes
    selectable only when a caller registers it as available and supplies a
    provider or concrete content IDs.
    """

    def __init__(self, entries: Iterable[Mapping[str, Any]] | None = None) -> None:
        self._entries: dict[str, dict[str, Any]] = {
            representation_id: {
                "representation_id": representation_id,
                "status": "unavailable",
                "provider_id": None,
                "content_ids": [],
                "reason": "No representation delivery provider or concept-grounded content source is implemented in this repository.",
            }
            for representation_id in REPRESENTATION_IDS
        }
        if entries:
            for entry in entries:
                self.register(**dict(entry))

    @property
    def taxonomy_version(self) -> str:
        return TAXONOMY_VERSION

    def register(
        self,
        representation_id: str,
        status: str,
        *,
        provider_id: str | None = None,
        content_ids: Iterable[str] = (),
        reason: str,
    ) -> None:
        if representation_id not in REPRESENTATION_IDS:
            raise ValueError(f"unknown representation category: {representation_id}")
        if status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        normalized_content_ids = sorted({str(item) for item in content_ids if str(item)})
        if status == "available" and not (provider_id or normalized_content_ids):
            raise ValueError("available capabilities require a provider_id or at least one content_id")
        if not reason.strip():
            raise ValueError("capability reason must be nonempty")
        self._entries[representation_id] = {
            "representation_id": representation_id,
            "status": status,
            "provider_id": provider_id,
            "content_ids": normalized_content_ids,
            "reason": reason.strip(),
        }

    def get(self, representation_id: str) -> dict[str, Any]:
        if representation_id not in self._entries:
            raise ValueError(f"unknown representation category: {representation_id}")
        return deepcopy(self._entries[representation_id])

    def is_available(self, representation_id: str) -> bool:
        return self._entries[representation_id]["status"] == "available"

    def as_dict(self) -> dict[str, Any]:
        return {
            "taxonomy_version": TAXONOMY_VERSION,
            "capabilities": [deepcopy(self._entries[item]) for item in REPRESENTATION_IDS],
        }
