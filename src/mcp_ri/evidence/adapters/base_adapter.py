"""Small protocol marker shared by evidence adapters."""

from __future__ import annotations

from typing import Any, Protocol


class EvidenceAdapter(Protocol):
    def from_reference(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...
