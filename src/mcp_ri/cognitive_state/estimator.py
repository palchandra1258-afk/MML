"""Rule-based, evidence-linked provisional cognitive-state estimates.

The estimator projects Phase 9 behavioral summaries into cautious status
categories. It does not infer or diagnose a psychological construct.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from ..evidence.evidence_schema import validate_conflict, validate_evidence
from ..learner_state.state_schema import validate_state as validate_behavioral_state
from .state_schema import validate_cognitive_state


EXPECTED_MODALITIES = ("text", "audio", "visual", "interaction", "temporal_history")
MIN_ATTEMPTS_FOR_PATTERN = 5
MIN_ATTEMPTS_FOR_CONSISTENT = 20
LOW_OBSERVED_ACCURACY_THRESHOLD = 0.50
CONSISTENT_ACCURACY_THRESHOLD = 0.80
CONSISTENT_WILSON_WIDTH_MAX = 0.40

LIMITATIONS = [
    "Estimated learning statuses are provisional behavioral categories, not validated cognitive or psychological states.",
    "EdNet correctness and skill tags describe response outcomes and item metadata; neither is a direct understanding or misconception label.",
    "The 0.50 low-performance and 0.80 relatively-consistent thresholds are transparent operational rules, not educationally validated cutoffs.",
    "The minimum counts reuse Phase 9 evidence tiers; its Beta smoothing and Wilson interval definitions are unchanged.",
    "Estimate confidence is capped at low when no construct-valid cognitive labels or independent annotations are available.",
    "Potential-difficulty hypotheses trigger investigation only; no misconception is inferred or declared.",
    "Missing text, audio, and visual data increase modality uncertainty and are not treated as negative observations.",
    "EdNet timestamps are shifted question-given times; sequence order is more defensible than absolute calendar interpretation.",
]


def _stable_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return prefix + hashlib.sha256(encoded).hexdigest()[:32]


def _support_level(performance: Mapping[str, Any]) -> str:
    sufficiency = performance.get("evidence_sufficiency")
    if sufficiency == "high":
        return "high"
    if sufficiency == "moderate":
        return "moderate"
    return "low"


def _available_modalities(evidence_records: Sequence[Mapping[str, Any]]) -> set[str]:
    available: set[str] = set()
    for record in evidence_records:
        if record["processing"]["status"] in {"reference_only", "failed"}:
            continue
        flags = set(record["processing"].get("quality_flags", []))
        if any(flag.endswith("_asset_not_available_for_inspection") for flag in flags):
            continue
        available.add(record["evidence_type"])
    return available


def _status(concept: Mapping[str, Any], contradictory: Sequence[str]) -> tuple[str, str]:
    attempts = concept["attempts"]
    accuracy = concept["historical_accuracy"]
    recent = concept["recent_accuracy"]
    trend = concept["performance_trend"]
    issues = set(concept["potential_issues"])
    if contradictory:
        return "requires_diagnostic_investigation", "Conflicting source evidence is retained; the engine cannot determine which account is correct."
    if attempts < MIN_ATTEMPTS_FOR_PATTERN:
        return "insufficient_evidence", f"Only {attempts} labeled responses are available; fewer than {MIN_ATTEMPTS_FOR_PATTERN} are used for a provisional pattern category."
    pattern_flags = issues & {
        "repeated_recent_incorrect_responses",
        "recent_performance_decline",
        "inconsistent_recent_responses",
    }
    if pattern_flags or (accuracy is not None and accuracy <= LOW_OBSERVED_ACCURACY_THRESHOLD):
        return "possible_difficulty", "Observed response history suggests that this concept may require further investigation; it does not establish a cognitive cause."
    interval = concept["uncertainty_interval_95"]
    interval_width = interval[1] - interval[0]
    if (
        attempts >= MIN_ATTEMPTS_FOR_CONSISTENT
        and accuracy is not None and accuracy >= CONSISTENT_ACCURACY_THRESHOLD
        and recent is not None and recent >= CONSISTENT_ACCURACY_THRESHOLD
        and trend in {"stable", "improving"}
        and not issues
        and interval_width <= CONSISTENT_WILSON_WIDTH_MAX
    ):
        return "relatively_consistent_performance", "Observed correctness is relatively consistent under the documented count, accuracy, trend, and Wilson-width rules."
    return "developing_performance", "The observed response pattern does not meet the rule for insufficient evidence, possible difficulty, or relatively consistent performance."


def _hypothesis(
    learner_id: str,
    concept_id: str | None,
    kind: str,
    supporting_ids: Sequence[str],
    contradictory_ids: Sequence[str],
    support_level: str,
    reason: str,
    statement: str,
) -> dict[str, Any]:
    supports = sorted(set(supporting_ids))
    contrad = sorted(set(contradictory_ids))
    hypothesis_id = _stable_id("hyp_", [learner_id, concept_id, kind, supports, contrad])
    return {
        "hypothesis_id": hypothesis_id,
        "concept_id": concept_id,
        "hypothesis_type": kind,
        "supporting_evidence_ids": supports,
        "contradictory_evidence_ids": contrad,
        "confidence_or_support_level": support_level,
        "uncertainty_reason": [reason],
        "investigation_status": "recommended",
        "statement": statement,
    }


def _recommendation(
    concept_id: str | None,
    action: str,
    reason: str,
    hypothesis_ids: Sequence[str],
    evidence_ids: Sequence[str],
) -> dict[str, Any]:
    supports = sorted(set(evidence_ids))
    hypotheses = sorted(set(hypothesis_ids))
    recommendation_id = _stable_id("dr_", [concept_id, action, reason, hypotheses, supports])
    return {
        "recommendation_id": recommendation_id,
        "concept_id": concept_id,
        "action": action,
        "reason": reason,
        "supporting_hypothesis_ids": hypotheses,
        "supporting_evidence_ids": supports,
        "status": "recommended",
    }


def _uncertainty(
    evidence_records: Sequence[Mapping[str, Any]],
    conflicts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not evidence_records:
        evidence_level = "unknown"
        evidence_reasons = ["No normalized evidence records were supplied."]
    elif conflicts:
        evidence_level = "high"
        evidence_reasons = ["One or more unresolved conflict records involve the supplied evidence."]
    else:
        evidence_level = "high"
        evidence_reasons = ["The available records do not provide validated cognitive-state labels."]

    interactions = [record for record in evidence_records if record["evidence_type"] == "interaction"]
    if not interactions:
        temporal_level = "unknown"
        temporal_reasons = ["No interaction event sequence was supplied."]
    elif all(
        record["temporal"].get("sequence_number") is not None
        and record["temporal"].get("event_timestamp") is not None
        for record in interactions
    ):
        temporal_level = "medium"
        temporal_reasons = ["Source order is available, but EdNet timestamps are shifted question-given times rather than response-submission times."]
    else:
        temporal_level = "high"
        temporal_reasons = ["One or more interaction events lack source sequence or event-time information."]

    present = _available_modalities(evidence_records)
    missing_modalities = set(EXPECTED_MODALITIES) - present
    if not evidence_records:
        modality_level = "unknown"
        modality_reasons = ["No modality evidence was supplied."]
    elif not missing_modalities:
        modality_level = "low"
        modality_reasons = []
    elif len(missing_modalities) >= 2:
        modality_level = "high"
        modality_reasons = ["Multiple expected modalities are absent: " + ", ".join(sorted(missing_modalities)) + "."]
    else:
        modality_level = "medium"
        modality_reasons = ["At least one expected modality is absent: " + ", ".join(sorted(missing_modalities)) + "."]

    inference_level = "high"
    inference_reasons = ["No construct-valid cognitive-state ground truth is available to calibrate this inference."]
    ranks = {"low": 0, "medium": 1, "high": 2, "unknown": 3}
    dimensions = {
        "evidence_uncertainty": evidence_level,
        "temporal_uncertainty": temporal_level,
        "modality_uncertainty": modality_level,
        "inference_uncertainty": inference_level,
    }
    overall = max(dimensions.values(), key=lambda item: ranks[item])
    reasons = {
        "evidence": evidence_reasons,
        "temporal": temporal_reasons,
        "modality": modality_reasons,
        "inference": inference_reasons,
        "overall": ["Overall uncertainty is the most conservative of the four separate uncertainty dimensions."],
    }
    return {**dimensions, "overall_uncertainty": overall, "uncertainty_reasons": reasons}


def estimate_cognitive_state(
    behavioral_state: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]],
    *,
    conflicts: Sequence[Mapping[str, Any]] = (),
    sequence_start: int | None = None,
    sequence_end: int | None = None,
) -> dict[str, Any]:
    """Project a Phase 9 state and Phase 10 evidence into a cautious estimate.

    The caller supplies an already-cutoff Phase 9 snapshot. If sequence bounds
    are provided, evidence after ``sequence_end`` is rejected to prevent a
    future event from entering a historical state.
    """
    validate_behavioral_state(behavioral_state)
    learner_id = behavioral_state["learner_id"]
    records = [dict(record) for record in evidence_records]
    for record in records:
        validate_evidence(record)
        if record["learner_id"] != learner_id:
            raise ValueError("all cognitive-state evidence must belong to the Phase 9 learner")
        seq = record["temporal"].get("sequence_number")
        if sequence_end is not None and seq is not None and seq > sequence_end:
            raise ValueError("evidence after the cognitive-state sequence cutoff is not allowed")
        if sequence_start is not None and seq is not None and seq < sequence_start:
            raise ValueError("evidence before sequence_start is outside the requested observation window")
    conflict_records = [dict(conflict) for conflict in conflicts]
    record_ids = {record["evidence_id"] for record in records}
    for conflict in conflict_records:
        validate_conflict(conflict)
        if set(conflict["evidence_ids"]) - record_ids:
            raise ValueError("conflict evidence IDs must refer to supplied evidence records")

    ordered_records = sorted(
        records,
        key=lambda item: (
            item["temporal"].get("sequence_number") is None,
            item["temporal"].get("sequence_number") if item["temporal"].get("sequence_number") is not None else 0,
        ),
    )
    evidence_references = [
        {
            "evidence_id": record["evidence_id"],
            "evidence_type": record["evidence_type"],
            "source_dataset": record["provenance"]["source_dataset"],
            "source_file": record["provenance"]["source_file"],
            "source_record_id": record["provenance"]["source_record_id"],
            "event_timestamp": record["temporal"]["event_timestamp"],
            "sequence_number": record["temporal"]["sequence_number"],
        }
        for record in ordered_records
    ]
    reference_ids = {reference["evidence_id"] for reference in evidence_references}
    phase9_summary = behavioral_state["observation_summary"]
    phase9_performance = behavioral_state["learning_performance"]
    phase9_concepts = {concept["concept_id"]: concept for concept in behavioral_state["concept_states"]}
    interactions = [record for record in ordered_records if record["evidence_type"] == "interaction"]
    if len(interactions) != phase9_summary["total_interactions"]:
        raise ValueError("complete interaction evidence is required to trace the Phase 9 observation summary")
    evidenced_label_count = sum(
        1 for record in interactions if record["content"].get("correctness") in (0, 1)
    )
    if evidenced_label_count != phase9_summary["labelled_responses"]:
        raise ValueError("interaction evidence labels do not match the Phase 9 labeled-response count")
    interaction_sequences = [record["temporal"].get("sequence_number") for record in interactions]
    if interaction_sequences and all(sequence is not None for sequence in interaction_sequences):
        numeric_sequences = [int(sequence) for sequence in interaction_sequences]
        if len(set(numeric_sequences)) != len(numeric_sequences):
            raise ValueError("interaction evidence contains repeated source sequence numbers")
        if max(numeric_sequences) - min(numeric_sequences) + 1 != len(numeric_sequences):
            raise ValueError("interaction evidence sequence has gaps; the Phase 9 prefix is not fully traceable")
        if sequence_start is not None and sequence_start != min(numeric_sequences):
            raise ValueError("sequence_start does not match the supplied interaction prefix")
        if sequence_end is not None and sequence_end != max(numeric_sequences):
            raise ValueError("sequence_end does not match the supplied interaction prefix")
    last_nonmissing_timestamp = next(
        (record["temporal"].get("event_timestamp") for record in reversed(interactions)
         if record["temporal"].get("event_timestamp") is not None),
        None,
    )
    if behavioral_state["state_timestamp"] != last_nonmissing_timestamp:
        raise ValueError("Phase 9 state_timestamp does not match the supplied chronological evidence prefix")
    if sequence_start is None:
        known_sequences = [sequence for sequence in interaction_sequences if sequence is not None]
        sequence_start = min(known_sequences) if known_sequences else None
    if sequence_end is None:
        known_sequences = [sequence for sequence in interaction_sequences if sequence is not None]
        sequence_end = max(known_sequences) if known_sequences else None

    event_times = [record["temporal"]["event_timestamp"] for record in interactions]
    first_event_time = event_times[0] if event_times else None
    last_event_time = event_times[-1] if event_times else None
    evidence_concepts: dict[str, set[str]] = {}
    concept_evidence_ids: dict[str, list[str]] = {}
    for record in interactions:
        for concept_id in record["content"].get("skill_ids", []):
            evidence_concepts.setdefault(record["evidence_id"], set()).add(concept_id)
            concept_evidence_ids.setdefault(concept_id, []).append(record["evidence_id"])

    conflict_ids_by_concept: dict[str, set[str]] = {}
    conflict_evidence_by_concept: dict[str, set[str]] = {}
    conflicts_without_concept: list[Mapping[str, Any]] = []
    for conflict in conflict_records:
        touched_concepts: set[str] = set()
        for evidence_id in conflict["evidence_ids"]:
            touched_concepts.update(evidence_concepts.get(evidence_id, set()))
        if not touched_concepts:
            conflicts_without_concept.append(conflict)
        for concept_id in touched_concepts:
            conflict_ids_by_concept.setdefault(concept_id, set()).add(conflict["conflict_id"])
            conflict_evidence_by_concept.setdefault(concept_id, set()).update(conflict["evidence_ids"])

    concept_estimates: list[dict[str, Any]] = []
    hypotheses: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    for concept_id in sorted(phase9_concepts):
        concept = phase9_concepts[concept_id]
        supporting_ids = sorted(set(concept_evidence_ids.get(concept_id, [])))
        concept_labelled_count = sum(
            1 for record in interactions
            if concept_id in record["content"].get("skill_ids", [])
            and record["content"].get("correctness") in (0, 1)
        )
        if concept_labelled_count != concept["attempts"]:
            raise ValueError(f"complete interaction evidence does not match Phase 9 attempts for {concept_id}")
        contradictory_ids = sorted(conflict_evidence_by_concept.get(concept_id, set()))
        status, rationale = _status(concept, contradictory_ids)
        observed = {
            "attempts": concept["attempts"],
            "correct": concept["correct"],
            "incorrect": concept["incorrect"],
            "historical_accuracy": concept["historical_accuracy"],
            "recent_accuracy": concept["recent_accuracy"],
            "smoothed_performance": concept["smoothed_performance"],
            "performance_trend": concept["performance_trend"],
            "performance_change": concept["performance_change"],
            "uncertainty_interval_95": concept["uncertainty_interval_95"],
            "phase9_evidence_sufficiency": concept["evidence_sufficiency"],
            "phase9_behavioral_confidence": concept["estimate_confidence"],
            "phase9_uncertainty_level": concept["uncertainty_level"],
            "potential_issues": list(concept["potential_issues"]),
        }
        concept_estimates.append({
            "concept_id": concept_id,
            "observed_performance": observed,
            "estimated_learning_status": status,
            "estimate_confidence": "low",
            "confidence_scope": "support_for_provisional_behavioral_category_not_cognitive_probability",
            "evidence_sufficiency": concept["evidence_sufficiency"],
            "uncertainty_level": "high",
            "supporting_evidence_ids": supporting_ids,
            "contradictory_evidence_ids": contradictory_ids,
            "estimation_method": "transparent_phase9_behavioral_rule_projection_v1",
            "rationale": rationale,
        })

        support_level = _support_level(concept)
        flags = set(concept["potential_issues"])
        concept_hypotheses: list[dict[str, Any]] = []
        if concept["attempts"] < MIN_ATTEMPTS_FOR_PATTERN and supporting_ids:
            concept_hypotheses.append(_hypothesis(
                learner_id, concept_id, "insufficient_concept_evidence", supporting_ids, [], "low",
                f"Only {concept['attempts']} labeled responses are available; the rule requires {MIN_ATTEMPTS_FOR_PATTERN}.",
                "There is not enough labeled response history to characterize this concept's performance.",
            ))
        if "repeated_recent_incorrect_responses" in flags and supporting_ids:
            concept_hypotheses.append(_hypothesis(
                learner_id, concept_id, "repeated_incorrect_responses", supporting_ids, [], support_level,
                "Phase 9 flags a recent run with at least three incorrect responses in its recent concept window.",
                "Observed recent responses include repeated incorrect answers; this may warrant a diagnostic check.",
            ))
        if concept["performance_trend"] == "declining" and supporting_ids:
            concept_hypotheses.append(_hypothesis(
                learner_id, concept_id, "declining_recent_performance", supporting_ids, [], support_level,
                "The latest-five versus preceding-five response-accuracy change crossed the Phase 9 -0.10 threshold.",
                "Observed recent response performance declined under the Phase 9 trend rule; the cause is unknown.",
            ))
        if "inconsistent_recent_responses" in flags and supporting_ids:
            concept_hypotheses.append(_hypothesis(
                learner_id, concept_id, "inconsistent_responses", supporting_ids, [], support_level,
                "The Phase 9 recent concept window contains a mixed pattern of correct and incorrect responses.",
                "Observed responses vary within the recent window; this is a reason to gather more evidence, not a diagnosis.",
            ))
        if contradictory_ids:
            concept_hypotheses.append(_hypothesis(
                learner_id, concept_id, "conflicting_evidence", supporting_ids or contradictory_ids,
                contradictory_ids, "low",
                "The source evidence is inconsistent and no automatic source-priority rule is justified.",
                "Conflicting evidence about this concept is preserved for investigation; no source is treated as authoritative.",
            ))
        for record in ordered_records:
            if record["evidence_type"] not in {"text", "audio", "visual"}:
                continue
            for annotation in record["content"].get("human_annotations", []):
                if (
                    isinstance(annotation, Mapping)
                    and annotation.get("annotation_type") == "human"
                    and annotation.get("hypothesis_type") == "possible_representation_difficulty"
                    and annotation.get("concept_id") == concept_id
                    and annotation.get("annotator_id")
                    and annotation.get("annotation_method")
                ):
                    concept_hypotheses.append(_hypothesis(
                        learner_id, concept_id, "possible_representation_difficulty", [record["evidence_id"]], [], "low",
                        "A caller-supplied human annotation is available, but this estimator does not independently validate it.",
                        "A human annotation suggests possible difficulty with a representation; gather more evidence before drawing a conclusion.",
                    ))
        hypotheses.extend(concept_hypotheses)

        if status == "insufficient_evidence":
            recommendations.append(_recommendation(
                concept_id, "present_diagnostic_question",
                "A short concept-aligned question would add direct response evidence because the current labeled count is small.",
                [item["hypothesis_id"] for item in concept_hypotheses], supporting_ids,
            ))
        elif status in {"possible_difficulty", "requires_diagnostic_investigation"}:
            action = "ask_for_clarification" if contradictory_ids else "ask_for_explanation"
            reason = "Ask the learner to explain or clarify the observed response so the source disagreement can be examined." if contradictory_ids else "Ask the learner to explain the reasoning behind a response pattern that triggered the provisional rule."
            recommendations.append(_recommendation(
                concept_id, action, reason,
                [item["hypothesis_id"] for item in concept_hypotheses],
                supporting_ids + contradictory_ids,
            ))
        representation_hypotheses = [item for item in concept_hypotheses if item["hypothesis_type"] == "possible_representation_difficulty"]
        if representation_hypotheses:
            recommendations.append(_recommendation(
                concept_id, "ask_for_explanation",
                "Ask the learner to explain or show their approach so the caller-supplied representation annotation can be investigated.",
                [item["hypothesis_id"] for item in representation_hypotheses],
                [evidence_id for item in representation_hypotheses for evidence_id in item["supporting_evidence_ids"]],
            ))

    for conflict in conflicts_without_concept:
        conflict_hypothesis = _hypothesis(
            learner_id, None, "conflicting_evidence", conflict["evidence_ids"], conflict["evidence_ids"], "low",
            "The conflict has no validated concept mapping, so it cannot support a concept-specific estimate.",
            "Evidence records disagree without a validated concept mapping; retain both and request clarification if relevant.",
        )
        hypotheses.append(conflict_hypothesis)
        recommendations.append(_recommendation(
            None, "ask_for_clarification", "Clarification can help a researcher understand the unresolved source disagreement.",
            [conflict_hypothesis["hypothesis_id"]], conflict["evidence_ids"],
        ))

    if not concept_estimates and interactions:
        recommendations.append(_recommendation(
            None, "present_diagnostic_question",
            "No Phase 9 skill concept is mapped for this evidence; a short diagnostic can add interpretable, task-linked observations.",
            [], [interactions[-1]["evidence_id"]],
        ))

    present_modalities = sorted(_available_modalities(ordered_records))
    missing_modalities = sorted(set(EXPECTED_MODALITIES) - set(present_modalities))
    conflict_ids = sorted(conflict["conflict_id"] for conflict in conflict_records)
    contradictory_source_ids = sorted({evidence_id for conflict in conflict_records for evidence_id in conflict["evidence_ids"]})
    provenance_keys: set[tuple[str, str | None, str, str]] = set()
    source_provenance = []
    for record in ordered_records:
        provenance = record["provenance"]
        key = (provenance["source_dataset"], provenance["source_file"], provenance["source_modality"], provenance["processing_method"])
        if key in provenance_keys:
            continue
        provenance_keys.add(key)
        source_provenance.append({
            "source_dataset": provenance["source_dataset"],
            "source_file": provenance["source_file"],
            "source_modality": provenance["source_modality"],
            "processing_method": provenance["processing_method"],
        })
    uncertainty = _uncertainty(ordered_records, conflict_records)
    overall_performance = behavioral_state["learning_performance"]
    observation_window = {
        "type": "chronological_prefix",
        "interaction_event_count": phase9_summary["total_interactions"],
        "labelled_event_count": phase9_summary["labelled_responses"],
        "sequence_start": sequence_start,
        "sequence_end": sequence_end,
        "timestamp_start": first_event_time,
        "timestamp_end": last_event_time,
    }
    state_id = _stable_id("cs_", [
        learner_id, behavioral_state["state_timestamp"], sequence_start, sequence_end,
        sorted(reference_ids), conflict_ids,
    ])
    state = {
        "schema_version": "1.0",
        "cognitive_state_id": state_id,
        "learner_id": learner_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_timestamp": behavioral_state["state_timestamp"],
        "state_version": 1,
        "previous_state_id": None,
        "observation_window": observation_window,
        "relevant_concept_ids": sorted(phase9_concepts),
        "evidence_references": evidence_references,
        "observed_evidence_summary": {
            "interaction_event_count": phase9_summary["total_interactions"],
            "labelled_response_count": phase9_summary["labelled_responses"],
            "historical_correctness": overall_performance["historical_performance"],
            "recent_correctness": overall_performance["recent_performance"],
            "performance_trend": overall_performance["performance_trend"],
            "available_modalities": present_modalities,
            "missing_modalities": missing_modalities,
            "contradictory_evidence_count": len(conflict_ids),
            "contradictory_evidence_ids": conflict_ids,
            "contradictory_source_evidence_ids": contradictory_source_ids,
            "source_provenance": source_provenance,
            "phase9_state_reference": {
                "schema_version": behavioral_state["schema_version"],
                "state_timestamp": behavioral_state["state_timestamp"],
            },
        },
        "concept_estimates": concept_estimates,
        "possible_difficulty_hypotheses": hypotheses,
        "uncertainty": uncertainty,
        "diagnostic_recommendations": recommendations,
        "state_change_summary": {
            "concept_status_changes": [],
            "hypothesis_ids_added": [],
            "hypothesis_ids_no_longer_emitted": [],
            "evidence_ids_added": sorted(reference_ids),
            "change_notes": ["Initial estimate; no prior cognitive-state record was supplied."],
        },
        "limitations": list(LIMITATIONS),
    }
    validate_cognitive_state(state)
    return state
