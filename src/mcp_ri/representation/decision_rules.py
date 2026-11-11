"""Transparent policy rules used by the representation decision engine."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .availability_registry import RepresentationAvailabilityRegistry
from .representation_taxonomy import REPRESENTATION_IDS


def _human_representation_claims(
    concept_id: str,
    hypotheses: Sequence[Mapping[str, Any]],
    evidence_records: Sequence[Mapping[str, Any]],
) -> list[tuple[str, str | None, str]]:
    mismatch_hypothesis_ids = {
        item["hypothesis_id"] for item in hypotheses
        if item["concept_id"] == concept_id and item["hypothesis_type"] == "possible_representation_difficulty"
    }
    if not mismatch_hypothesis_ids:
        return []
    allowed = set(REPRESENTATION_IDS)
    claims: list[tuple[str, str | None, str]] = []
    for record in evidence_records:
        if record.get("evidence_type") not in {"text", "audio", "visual"}:
            continue
        for annotation in record.get("content", {}).get("human_annotations", []):
            if (
                annotation.get("annotation_type") == "human"
                and annotation.get("hypothesis_type") == "possible_representation_difficulty"
                and annotation.get("concept_id") == concept_id
                and annotation.get("annotator_id")
                and annotation.get("annotation_method")
            ):
                representation_id = annotation.get("representation_id") or annotation.get("affected_representation")
                if representation_id in allowed:
                    suggested = annotation.get("suggested_alternative_representation")
                    if suggested not in allowed or suggested == representation_id:
                        suggested = None
                    claims.append((representation_id, suggested, record["evidence_id"]))
    return sorted(set(claims))


def evaluate_decision_rules(
    cognitive_state: Mapping[str, Any],
    concept_id: str,
    registry: RepresentationAvailabilityRegistry,
    *,
    evidence_records: Sequence[Mapping[str, Any]] = (),
    current_representation: str | None = None,
) -> dict[str, Any]:
    estimates = {item["concept_id"]: item for item in cognitive_state["concept_estimates"]}
    estimate = estimates.get(concept_id)
    hypotheses = [
        item for item in cognitive_state["possible_difficulty_hypotheses"]
        if item["concept_id"] in {None, concept_id}
    ]
    concept_hypotheses = [item for item in hypotheses if item["concept_id"] == concept_id]
    observed = estimate["observed_performance"] if estimate else {}
    attempts = int(observed.get("attempts", 0))
    statuses = {item["hypothesis_type"] for item in concept_hypotheses}
    flags = set(observed.get("potential_issues", []))
    supporting_ids = sorted(set(estimate["supporting_evidence_ids"])) if estimate else []
    contradictory_ids = sorted(set(estimate["contradictory_evidence_ids"])) if estimate else []
    supporting_ids = sorted(set(supporting_ids) | {
        evidence_id for item in concept_hypotheses for evidence_id in item["supporting_evidence_ids"]
    })
    if not estimate:
        supporting_ids = sorted({
            reference["evidence_id"]
            for reference in cognitive_state["evidence_references"]
            if reference["evidence_type"] in {"interaction", "temporal_history"}
        })
        contradictory_ids = sorted(set(
            cognitive_state["observed_evidence_summary"]["contradictory_source_evidence_ids"]
        ))
    rule_evidence = sorted(set(supporting_ids) | set(contradictory_ids))

    missing_estimate = estimate is None
    insufficient_evidence = (
        missing_estimate
        or estimate["estimated_learning_status"] == "insufficient_evidence"
        or estimate["evidence_sufficiency"] in {"none", "low"}
        or attempts < 5
    )
    repeated = "repeated_incorrect_responses" in statuses or "repeated_recent_incorrect_responses" in flags
    declining = "declining_recent_performance" in statuses or observed.get("performance_trend") == "declining"
    inconsistent = "inconsistent_responses" in statuses or "inconsistent_recent_responses" in flags
    insufficient_coverage = missing_estimate or not supporting_ids or attempts == 0
    representation_difficulty = "possible_representation_difficulty" in statuses
    conflicting = bool(contradictory_ids) or (
        estimate is not None and estimate["estimated_learning_status"] == "requires_diagnostic_investigation"
    ) or "conflicting_evidence" in statuses

    conditions: dict[str, tuple[bool, str]] = {
        "concept_estimate_present": (not missing_estimate, "A Phase 11 estimate exists for the requested concept."),
        "minimum_response_coverage": (attempts >= 5, f"The concept has {attempts} labeled attempts; the operational floor is 5."),
        "concept_evidence_coverage": (not insufficient_coverage, "Concept-linked response evidence is present for the requested target."),
        "repeated_incorrect_hypothesis": (repeated, "Phase 11 records a repeated-incorrect pattern hypothesis or flag."),
        "declining_performance": (declining, "Phase 11 records a declining trend for the concept."),
        "inconsistent_responses": (inconsistent, "Phase 11 records an inconsistent-response pattern."),
        "explicit_representation_hypothesis": (representation_difficulty, "A caller-supplied human annotation supports a possible representation-difficulty hypothesis."),
        "contradictory_evidence": (conflicting, "The concept has unresolved contradictory evidence that must remain visible."),
    }
    trace = []
    for rule_id, (met, explanation) in conditions.items():
        trace.append({
            "rule_id": rule_id,
            "conditions_satisfied": [explanation] if met else [],
            "conditions_not_satisfied": [] if met else [explanation],
            "evidence_ids": rule_evidence if met else [],
            "explanation": explanation,
        })

    claims = _human_representation_claims(concept_id, concept_hypotheses, evidence_records)
    trace.append({
        "rule_id": "representation_subtype_evidence",
        "conditions_satisfied": [
            f"Human annotation identifies affected representation '{affected}'."
            + (f" and suggests '{suggested}' as an alternative." if suggested else "")
            for affected, suggested, _ in claims
        ],
        "conditions_not_satisfied": [] if any(suggested for _, suggested, _ in claims) else [
            "No human annotation identifies a supported alternative representation; no modality-specific change can be justified."
        ],
        "evidence_ids": sorted({evidence_id for _, _, evidence_id in claims}),
        "explanation": "A representation category is changed only when a caller-provided human annotation names it; EdNet response outcomes do not establish modality difficulty or preference.",
    })

    # Scenario rules prioritize collecting clarifying evidence when coverage,
    # consistency, or source agreement is weak. Candidate content types are
    # selected only if a provider/content source is registered as available.
    ordered_candidates: list[tuple[str, str]] = []
    selected_action = "defer_until_capability_available"
    decision_reason = "No decision rule supports a change, and the current capability registry has no executable representation provider."
    plan_kind = "initial"

    if conflicting:
        ordered_candidates = [("diagnostic", "A diagnostic question is preferred to resolve retained source disagreement.")]
        selected_action = "request_diagnostic_evidence"
        decision_reason = "Conflicting evidence is preserved. A diagnostic question or clarification is recommended before changing the representation."
        plan_kind = "diagnostic"
    elif insufficient_evidence or insufficient_coverage or inconsistent:
        ordered_candidates = [("diagnostic", "Sparse or inconsistent evidence calls for a low-commitment diagnostic observation.")]
        selected_action = "request_diagnostic_evidence"
        decision_reason = "The concept evidence is sparse or inconsistent; collect a diagnostic response or reasoning explanation before changing representation."
        plan_kind = "diagnostic"
    elif representation_difficulty:
        for affected, suggested, _ in claims:
            if suggested and suggested != current_representation:
                ordered_candidates.append((suggested, f"A human annotation names '{affected}' as a possible difficulty and explicitly suggests '{suggested}'; it remains a low-support candidate."))
        if not ordered_candidates:
            ordered_candidates = [("diagnostic", "The annotation does not identify a specific modality to change; request clarifying evidence." )]
        selected_action = "recommend_representation" if any(suggested for _, suggested, _ in claims) else "request_diagnostic_evidence"
        decision_reason = "A human annotation raises a possible representation mismatch. The annotation does not establish that another representation will improve learning; any alternative is provisional, and no general modality preference is inferred."
        plan_kind = "alternative"
    elif repeated and declining:
        ordered_candidates = [
            ("worked_example", "Repeated errors and a declining trend make a simpler worked example a candidate for investigation."),
            ("alternative_explanation", "The declining trend also warrants considering a genuinely different explanation."),
            ("textual", "A simplified wording is a candidate only if a content provider is available."),
            ("diagnostic", "A diagnostic question can check the response pattern and possible prerequisites."),
        ]
        if current_representation == "alternative_explanation":
            ordered_candidates = [item for item in ordered_candidates if item[0] != "alternative_explanation"]
        selected_action = "recommend_representation"
        decision_reason = "Repeated incorrect responses and a declining trend are both present. A simpler example or different explanation may be tested, but neither the cause nor effectiveness is established."
        plan_kind = "alternative"
    elif repeated:
        ordered_candidates = [
            ("worked_example", "Repeated incorrect responses make a step-by-step example a candidate for investigation, not a diagnosis."),
            ("textual", "A simplified wording is a candidate only if a content provider is available."),
            ("diagnostic", "A diagnostic question can clarify the response pattern."),
        ]
        selected_action = "recommend_representation"
        decision_reason = "Repeated incorrect responses support testing a worked example or simplified explanation, but do not identify the cause or establish effectiveness."
        plan_kind = "alternative"
    elif declining:
        ordered_candidates = [
            ("worked_example", "A simpler worked example is a candidate after declining observed performance."),
            ("alternative_explanation", "An alternative explanation is a candidate if it differs from the current explanation."),
            ("diagnostic", "A diagnostic prompt can check prerequisites and clarify the observed decline."),
        ]
        if "alternative_explanation" in {kind for kind, _ in ordered_candidates} and current_representation == "alternative_explanation":
            ordered_candidates = [item for item in ordered_candidates if item[0] != "alternative_explanation"]
        selected_action = "recommend_representation"
        decision_reason = "Recent performance declined under the Phase 9 rule. A simpler example or genuinely different explanation may be tested; prerequisites remain unknown."
        plan_kind = "alternative"
    else:
        if current_representation:
            ordered_candidates = [(current_representation, "Continue the recorded current representation because no difficulty rule requests a change.")]
            selected_action = "continue_current_representation"
            plan_kind = "continued"

    selected_representation = next(
        (candidate for candidate, _ in ordered_candidates if registry.is_available(candidate)),
        None,
    )
    if selected_representation is None:
        if ordered_candidates:
            unavailable = [registry.get(candidate) for candidate, _ in ordered_candidates]
            unavailable_summary = ", ".join(f"{item['representation_id']} ({item['status']})" for item in unavailable)
            decision_reason += f" No candidate can be selected for delivery because the registered capabilities are {unavailable_summary}."
        if selected_action == "recommend_representation":
            selected_action = "request_additional_evidence"
            plan_kind = "diagnostic"
        elif selected_action == "continue_current_representation":
            selected_action = "defer_until_capability_available"
            plan_kind = "continued"
        elif selected_action == "defer_until_capability_available" and (insufficient_evidence or insufficient_coverage):
            selected_action = "request_additional_evidence"
            plan_kind = "diagnostic"

    alternatives_trace = []
    candidate_reason = {candidate: reason for candidate, reason in ordered_candidates}
    for representation_id in REPRESENTATION_IDS:
        if representation_id == selected_representation:
            continue
        capability = registry.get(representation_id)
        if representation_id in candidate_reason:
            reason = candidate_reason[representation_id]
            if capability["status"] != "available":
                reason += f" It is recorded as {capability['status']}: {capability['reason']}"
        elif capability["status"] != "available":
            reason = f"Not considered for selection because this capability is {capability['status']}: {capability['reason']}"
        else:
            reason = "Not selected because the active rule does not provide evidence for preferring this category; no modality preference is inferred."
        alternatives_trace.append({
            "representation_id": representation_id,
            "availability_status": capability["status"],
            "selection_status": "rejected",
            "reason": reason,
        })
    if selected_representation is not None:
        decision_reason += f" The capability registry identifies '{selected_representation}' as available; the recommendation remains non-executing and low confidence."
        selected_action = "continue_current_representation" if selected_representation == current_representation and selected_action == "continue_current_representation" else "recommend_representation"
        capability_reference = registry.get(selected_representation)
        delivery_status = "available"
        if selected_representation not in candidate_reason:
            candidate_reason[selected_representation] = decision_reason
        plan_kind = "continued" if selected_action == "continue_current_representation" else plan_kind
        if selected_representation == "diagnostic":
            plan_kind = "diagnostic"
    else:
        capability_reference = None
        delivery_status = "not_selected"

    if declining:
        decision_reason += " Prerequisite knowledge is not present in the available metadata and should be checked before attributing the decline to a representation."

    return {
        "selected_representation": selected_representation,
        "selected_action": selected_action,
        "delivery_status": delivery_status,
        "capability_reference": capability_reference,
        "decision_reason": decision_reason,
        "plan_kind": plan_kind,
        "policy_trace": trace,
        "alternative_representations": alternatives_trace,
        "selected_candidate_reason": candidate_reason.get(selected_representation),
        "conditions": {
            "insufficient_evidence": insufficient_evidence,
            "insufficient_concept_coverage": insufficient_coverage,
            "repeated_incorrect_responses": repeated,
            "declining_recent_performance": declining,
            "inconsistent_responses": inconsistent,
            "possible_representation_difficulty": representation_difficulty,
            "conflicting_evidence": conflicting,
        },
        "supporting_evidence_ids": supporting_ids,
        "contradictory_evidence_ids": contradictory_ids,
        "diagnostic_recommendations": [
            item for item in cognitive_state["diagnostic_recommendations"]
            if item["concept_id"] in {None, concept_id}
        ],
        "concept_estimate": estimate,
        "human_representation_claims": claims,
    }
