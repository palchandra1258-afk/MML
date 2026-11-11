"""Adapter for references to existing Phase 9 behavioral learner states."""

from __future__ import annotations

from typing import Any, Mapping

from ..evidence_schema import validate_evidence
from ..normalizer import base_record


class TemporalHistoryAdapter:
    def from_learner_state(
        self,
        state: Mapping[str, Any],
        *,
        state_reference: str,
        related_evidence_ids: list[str] | None = None,
        source_dataset: str = "EdNet-KT1",
        source_file: str | None = None,
    ) -> dict[str, Any]:
        learner_id = str(state.get("learner_id", ""))
        if not learner_id:
            raise ValueError("Phase 9 state is missing learner_id")
        performance = dict(state.get("learning_performance", {}))
        summary = dict(state.get("observation_summary", {}))
        content = {
            "state_reference": state_reference,
            "state_schema_version": state.get("schema_version"),
            "state_timestamp": state.get("state_timestamp"),
            "observation_summary": summary,
            "performance_summary": {
                key: performance.get(key)
                for key in ("attempts", "correct", "incorrect", "historical_performance", "recent_performance", "performance_trend", "evidence_sufficiency", "uncertainty_level")
            },
            "concept_state_count": len(state.get("concept_states", [])),
        }
        record = base_record(
            learner_id=learner_id,
            session_id=None,
            evidence_type="temporal_history",
            event_timestamp=state.get("state_timestamp"),
            sequence_number=None,
            temporal_precision="unknown" if state.get("state_timestamp") else "not_available",
            timestamp_source="Phase 9 state source event timestamp; EdNet time is shifted and question-given",
            source_dataset=source_dataset,
            source_file=source_file,
            source_record_id=f"phase9:{learner_id}:{state_reference}",
            source_modality="derived",
            processing_method="reference_existing_phase9_behavioral_state_without_recomputing_it",
            content=content,
            extraction_method="state_reference_and_summary_projection",
            missing_fields=["state_timestamp"] if not state.get("state_timestamp") else [],
            uncertainty_flags=["behavioral_state_not_cognitive_state"],
            uncertainty_notes=["This record references Phase 9 response-history summaries; it is not a cognitive-state label."],
        )
        record["related_evidence_ids"] = sorted(set(related_evidence_ids or []))
        validate_evidence(record)
        return record
