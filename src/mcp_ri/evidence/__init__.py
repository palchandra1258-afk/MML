"""MCP-RI evidence records, adapters, conservative alignment and grouping."""

from .evidence_schema import validate_alignment, validate_conflict, validate_evidence, validate_group
from .grouping import group_evidence
from .normalizer import normalize_evidence
from .registry import EvidenceRegistry
from .state_bridge import apply_interaction_evidence, phase9_row_from_interaction

__all__ = [
    "EvidenceRegistry", "apply_interaction_evidence", "group_evidence",
    "normalize_evidence", "phase9_row_from_interaction", "validate_alignment", "validate_conflict", "validate_evidence", "validate_group",
]
