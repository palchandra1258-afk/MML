from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "representation"))

from mcp_ri.cognitive_state import CognitiveStateHistory, estimate_cognitive_state  # noqa: E402
from mcp_ri.evidence.adapters.interaction import InteractionAdapter  # noqa: E402
from mcp_ri.evidence.adapters.temporal import TemporalHistoryAdapter  # noqa: E402
from mcp_ri.evidence.adapters.text import TextAdapter  # noqa: E402
from mcp_ri.evidence.registry import EvidenceRegistry  # noqa: E402
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402
from mcp_ri.representation import (  # noqa: E402
    EdNetContentCatalog,
    RepresentationAvailabilityRegistry,
    RepresentationPlanHistory,
    build_representation_plan,
    taxonomy_document,
    validate_representation_plan,
)
from evaluate_representation_plans import evaluate  # noqa: E402


def build_fixture(
    labels: list[int],
    *,
    learner_id: str = "u-plan",
    annotation: dict | None = None,
    conflict: bool = False,
):
    accumulator = LearnerStateAccumulator(learner_id)
    adapter = InteractionAdapter()
    interactions = []
    for order, label in enumerate(labels):
        row = {
            "learner_id": learner_id,
            "source_row_order": str(order),
            "timestamp": str(2_000_000 + order * 1_000),
            "question_id": f"q{order + 1}",
            "solving_id": f"solve-{order}",
            "submitted_answer": "a" if label else "b",
            "correctness": str(label),
            "skill_tags": "7",
            "session_id": "session-1",
            "is_exact_duplicate": "0",
        }
        interactions.append(adapter.from_processed_row(row))
        accumulator.update(row)
    behavioral = accumulator.snapshot()
    evidence = list(interactions)
    if annotation:
        text = TextAdapter().from_text(
            learner_id,
            "A synthetic human-reviewed representation note.",
            source_record_id="annotation-1",
            human_annotations=[{
                "annotation_type": "human",
                "hypothesis_type": "possible_representation_difficulty",
                "concept_id": "ednet_skill:7",
                "annotator_id": "reviewer-synthetic",
                "annotation_method": "controlled_test_fixture",
                **annotation,
            }],
        )
        evidence.append(text)
    temporal = TemporalHistoryAdapter().from_learner_state(
        behavioral,
        state_reference=f"fixture:{learner_id}:{len(labels)}",
        related_evidence_ids=[item["evidence_id"] for item in interactions],
    )
    evidence.append(temporal)
    conflicts = []
    if conflict:
        registry = EvidenceRegistry()
        for item in evidence:
            registry.add(item)
        conflict_record = registry.add_conflict(
            [interactions[0]["evidence_id"], evidence[-2]["evidence_id"]],
            conflict_type="synthetic_disagreement",
            description="Controlled test-only disagreement.",
        )
        evidence = registry.records
        conflicts = [conflict_record]
    state = estimate_cognitive_state(behavioral, evidence, conflicts=conflicts)
    return state, behavioral, evidence


class RepresentationTaxonomyTests(unittest.TestCase):
    def test_taxonomy_is_versioned_and_has_requested_categories(self):
        document = taxonomy_document()
        ids = [item["representation_id"] for item in document["representations"]]
        self.assertEqual(document["taxonomy_version"], "1.0")
        self.assertEqual(set(ids), {"textual", "worked_example", "visual", "symbolic", "interactive", "simulation", "diagnostic", "alternative_explanation"})

    def test_registry_never_marks_missing_provider_available(self):
        registry = RepresentationAvailabilityRegistry()
        self.assertEqual(registry.get("visual")["status"], "unavailable")
        with self.assertRaisesRegex(ValueError, "require a provider_id"):
            registry.register("visual", "available", reason="No provider supplied")
        registry.register("visual", "available", provider_id="visual-demo", reason="Synthetic test provider")
        self.assertTrue(registry.is_available("visual"))


class RepresentationDecisionTests(unittest.TestCase):
    def build(self, labels, **kwargs):
        state, behavioral, evidence = build_fixture(labels, **kwargs)
        plan = build_representation_plan(
            state,
            "ednet_skill:7",
            behavioral_state=behavioral,
            evidence_records=evidence,
            teaching_context={"trajectory_id": f"trajectory:{state['learner_id']}:skill-7"},
        )
        validate_representation_plan(plan)
        return state, behavioral, evidence, plan

    def test_insufficient_evidence_requests_diagnostic_and_selects_no_unavailable_content(self):
        _, _, _, plan = self.build([1, 0])
        self.assertEqual(plan["decision"]["selected_action"], "request_diagnostic_evidence")
        self.assertIsNone(plan["decision"]["selected_representation"])
        self.assertEqual(plan["decision"]["delivery_status"], "not_selected")
        self.assertTrue(any(item["representation_id"] == "diagnostic" and item["availability_status"] == "unavailable" for item in plan["decision"]["alternative_representations"]))

    def test_repeated_incorrect_rule_considers_example_text_and_diagnostic_without_claiming_misconception(self):
        _, _, _, plan = self.build([0] * 5)
        alternatives = {item["representation_id"] for item in plan["decision"]["alternative_representations"]}
        self.assertTrue({"worked_example", "textual", "diagnostic"} <= alternatives)
        self.assertEqual(plan["decision"]["selected_action"], "request_additional_evidence")
        self.assertIn("do not identify the cause", plan["decision"]["decision_reason"])
        self.assertFalse(any("misconception" in item["rule_id"] for item in plan["decision"]["policy_trace"]))

    def test_available_content_can_be_selected_and_unavailable_alternatives_explain_why(self):
        state, behavioral, evidence = build_fixture([0] * 5)
        registry = RepresentationAvailabilityRegistry()
        registry.register("textual", "available", provider_id="simple-text-provider", reason="Synthetic provider registered for a test")
        plan = build_representation_plan(state, "ednet_skill:7", behavioral_state=behavioral, evidence_records=evidence, registry=registry)
        self.assertEqual(plan["decision"]["selected_representation"], "textual")
        self.assertEqual(plan["decision"]["delivery_status"], "available")
        self.assertEqual(plan["decision"]["capability_reference"]["provider_id"], "simple-text-provider")
        worked = next(item for item in plan["decision"]["alternative_representations"] if item["representation_id"] == "worked_example")
        self.assertEqual(worked["availability_status"], "unavailable")
        self.assertIn("No representation delivery provider", worked["reason"])

    def test_decline_can_choose_available_alternative_explanation_over_unavailable_example(self):
        state, behavioral, evidence = build_fixture([1] * 5 + [0] * 5)
        registry = RepresentationAvailabilityRegistry()
        registry.register("alternative_explanation", "available", provider_id="rephrase-provider", reason="Synthetic provider registered for a test")
        plan = build_representation_plan(state, "ednet_skill:7", behavioral_state=behavioral, evidence_records=evidence, registry=registry)
        self.assertEqual(plan["decision"]["selected_representation"], "alternative_explanation")
        self.assertEqual(plan["decision"]["delivery_status"], "available")

    def test_consistent_performance_can_continue_current_available_representation(self):
        state, behavioral, evidence = build_fixture([1] * 20)
        registry = RepresentationAvailabilityRegistry()
        registry.register("textual", "available", provider_id="text-provider", reason="Synthetic provider registered for a test")
        plan = build_representation_plan(
            state,
            "ednet_skill:7",
            behavioral_state=behavioral,
            evidence_records=evidence,
            registry=registry,
            teaching_context={"current_representation": "textual"},
        )
        self.assertEqual(plan["decision"]["selected_representation"], "textual")
        self.assertEqual(plan["decision"]["selected_action"], "continue_current_representation")
        self.assertEqual(plan["plan_kind"], "continued")

    def test_declining_performance_rule_records_prerequisite_check(self):
        _, _, _, plan = self.build([1] * 5 + [0] * 5)
        self.assertTrue(any(item["rule_id"] == "declining_performance" and item["conditions_satisfied"] for item in plan["decision"]["policy_trace"]))
        self.assertTrue(any(item["representation_id"] == "alternative_explanation" for item in plan["decision"]["alternative_representations"]))
        self.assertTrue(any(item["method"] == "prerequisite_check" for item in plan["evaluation_strategy"]) or "prerequisite" in plan["decision"]["decision_reason"])
        self.assertIn("Prerequisite knowledge is not present", plan["decision"]["decision_reason"])

    def test_inconsistent_responses_prefer_diagnostic_evidence(self):
        _, _, _, plan = self.build([1, 0] * 5)
        self.assertTrue(any(item["rule_id"] == "inconsistent_responses" and item["conditions_satisfied"] for item in plan["decision"]["policy_trace"]))
        self.assertIn(plan["decision"]["selected_action"], {"request_diagnostic_evidence", "request_additional_evidence"})
        self.assertEqual(plan["decision"]["selected_representation"], None)

    def test_missing_concept_coverage_defers_without_fabricating_grounding(self):
        state, _, _, = build_fixture([1] * 5)
        plan = build_representation_plan(state, "ednet_skill:999999")
        self.assertTrue(any(item["rule_id"] == "concept_estimate_present" and not item["conditions_satisfied"] for item in plan["decision"]["policy_trace"]))
        self.assertEqual(plan["concept_grounding"]["content_status"], "unavailable")
        self.assertIsNone(plan["decision"]["selected_representation"])

    def test_unresolved_conflict_is_preserved_and_blocks_representation_change(self):
        _, _, _, plan = self.build([1] * 5, conflict=True)
        self.assertTrue(plan["input_references"]["contradictory_evidence_ids"])
        conflict_rule = next(item for item in plan["decision"]["policy_trace"] if item["rule_id"] == "contradictory_evidence")
        self.assertTrue(conflict_rule["conditions_satisfied"])
        self.assertEqual(plan["decision"]["selected_action"], "request_diagnostic_evidence")
        self.assertIsNone(plan["decision"]["selected_representation"])

    def test_human_mismatch_annotation_can_support_an_available_alternative_without_preference_claim(self):
        state, behavioral, evidence = build_fixture(
            [1] * 5,
            annotation={"representation_id": "symbolic", "suggested_alternative_representation": "visual"},
        )
        registry = RepresentationAvailabilityRegistry()
        registry.register("visual", "available", content_ids=["synthetic-diagram-1"], reason="Synthetic test asset")
        plan = build_representation_plan(
            state,
            "ednet_skill:7",
            behavioral_state=behavioral,
            evidence_records=evidence,
            registry=registry,
            teaching_context={"current_representation": "symbolic"},
        )
        self.assertEqual(plan["decision"]["selected_representation"], "visual")
        self.assertEqual(plan["decision"]["decision_confidence"], "low")
        self.assertIn("does not establish that another representation will improve learning", plan["decision"]["decision_reason"])
        annotation_id = next(item["evidence_id"] for item in evidence if item["evidence_type"] == "text")
        self.assertIn(annotation_id, plan["input_references"]["supporting_evidence_ids"])
        self.assertIn("no general modality preference is inferred", plan["decision"]["decision_reason"])

    def test_mismatch_without_specific_alternative_requests_diagnostic_not_a_random_modality(self):
        state, behavioral, evidence = build_fixture([1] * 5, annotation={"representation_id": "symbolic"})
        registry = RepresentationAvailabilityRegistry()
        registry.register("visual", "available", provider_id="visual-test", reason="Synthetic provider")
        plan = build_representation_plan(state, "ednet_skill:7", behavioral_state=behavioral, evidence_records=evidence, registry=registry)
        self.assertIsNone(plan["decision"]["selected_representation"])
        self.assertEqual(plan["decision"]["selected_action"], "request_diagnostic_evidence")

    def test_planned_capability_is_not_selected_as_executable(self):
        state, behavioral, evidence = build_fixture(
            [1] * 5,
            annotation={"representation_id": "symbolic", "suggested_alternative_representation": "visual"},
        )
        registry = RepresentationAvailabilityRegistry()
        registry.register("visual", "planned", reason="Visualization work is planned but no renderer is registered")
        plan = build_representation_plan(state, "ednet_skill:7", behavioral_state=behavioral, evidence_records=evidence, registry=registry)
        self.assertIsNone(plan["decision"]["selected_representation"])
        visual = next(item for item in plan["decision"]["alternative_representations"] if item["representation_id"] == "visual")
        self.assertEqual(visual["availability_status"], "planned")

    def test_all_plan_decisions_are_traceable_to_cognitive_and_evidence_ids(self):
        state, _, _, plan = self.build([0] * 5)
        self.assertEqual(plan["input_references"]["cognitive_state_id"], state["cognitive_state_id"])
        known = {item["evidence_id"] for item in state["evidence_references"]}
        linked = set(plan["input_references"]["supporting_evidence_ids"] + plan["input_references"]["contradictory_evidence_ids"])
        self.assertTrue(linked)
        self.assertLessEqual(linked, known)
        for rule in plan["decision"]["policy_trace"]:
            self.assertLessEqual(set(rule["evidence_ids"]), linked)

    def test_recommendation_confidence_scope_does_not_claim_learning_effect(self):
        _, _, _, plan = self.build([1] * 5)
        self.assertEqual(plan["decision"]["decision_confidence"], "low")
        self.assertEqual(plan["decision"]["confidence_scope"], "support_for_recommendation_not_learning_effect_or_modality_preference")
        self.assertIn("does not infer learner modality preference", plan["limitations"]["claims_boundary"])

    def test_inconsistent_or_wrong_learner_inputs_are_rejected(self):
        state, _, evidence = build_fixture([1] * 5)
        _, other_behavioral, _ = build_fixture([1] * 5, learner_id="u-other")
        with self.assertRaisesRegex(ValueError, "belong to the cognitive-state learner"):
            build_representation_plan(state, "ednet_skill:7", behavioral_state=other_behavioral)
        unrelated = TextAdapter().from_text("u-plan", "Not referenced in this state.", source_record_id="unreferenced")
        with self.assertRaisesRegex(ValueError, "referenced by the supplied cognitive state"):
            build_representation_plan(state, "ednet_skill:7", evidence_records=[evidence[0], unrelated])


class GroundingAndHistoryTests(unittest.TestCase):
    def test_ednet_catalog_uses_skill_question_metadata_without_answer_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "content.zip"
            payload = "question_id,bundle_id,explanation_id,correct_answer,part,tags\nq-demo,b-demo,e-demo,secret,2,7;8\n"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("contents/questions.csv", payload)
                archive.writestr("contents/lectures.csv", "lecture_id,part,tags,video_length\nl-demo,3,7,42\n")
            catalog = EdNetContentCatalog.from_zip(archive_path)
            grounding = catalog.ground("ednet_skill:7")
        self.assertEqual(grounding.related_question_ids, ("q-demo",))
        self.assertEqual(grounding.parts, ("2", "3"))
        self.assertEqual(grounding.explanation_reference_ids, ("e-demo",))
        self.assertEqual(grounding.related_lecture_ids, ("l-demo",))
        self.assertEqual(grounding.lecture_parts, ("3",))
        self.assertEqual(grounding.lecture_video_length_values, ("42",))
        self.assertIsNone(grounding.concept_name)
        self.assertIsNone(grounding.learning_objective)
        self.assertEqual(grounding.example_ids, ())
        self.assertNotIn("correct_answer", json.dumps(grounding.as_dict()))

    def test_plan_history_appends_revised_plan_and_preserves_context_and_evidence(self):
        first_state, _, _ = build_fixture([1] * 5)
        second_state, _, _ = build_fixture([1] * 5 + [0] * 5)
        first = build_representation_plan(
            first_state, "ednet_skill:7",
            teaching_context={"current_representation": "textual", "trajectory_id": "trajectory-a", "branch_return_pointer": "lesson:3"},
        )
        history = RepresentationPlanHistory("u-plan", "ednet_skill:7")
        saved_first = history.append(first)
        revised = build_representation_plan(second_state, "ednet_skill:7", prior_plan=history.latest)
        saved_revised = history.append(revised)
        self.assertEqual(saved_revised["plan_version"], 2)
        self.assertEqual(saved_revised["previous_plan_id"], saved_first["plan_id"])
        self.assertEqual(saved_revised["plan_kind"], "revised")
        for key in ("current_concept_id", "current_learning_objective", "current_representation", "trajectory_id", "branch_return_pointer"):
            self.assertEqual(saved_revised["teaching_context"][key], saved_first["teaching_context"][key])
        self.assertTrue(set(saved_first["teaching_context"]["evidence_history_ids"]) <= set(saved_revised["teaching_context"]["evidence_history_ids"]))
        self.assertEqual(len(history.plans), 2)
        saved_first["decision"]["decision_reason"] = "caller mutation"
        self.assertNotEqual(history.plans[0]["decision"]["decision_reason"], "caller mutation")

    def test_plan_history_rejects_an_earlier_cognitive_state_version(self):
        first_state, _, _ = build_fixture([1] * 5)
        second_state, _, _ = build_fixture([1] * 5 + [0] * 5)
        cognitive_history = CognitiveStateHistory("u-plan")
        cognitive_history.append(first_state)
        latest_state = cognitive_history.append(second_state)
        latest_plan = build_representation_plan(latest_state, "ednet_skill:7")
        plan_history = RepresentationPlanHistory("u-plan", "ednet_skill:7")
        plan_history.append(latest_plan)
        earlier_plan = build_representation_plan(first_state, "ednet_skill:7", prior_plan=plan_history.latest)
        with self.assertRaisesRegex(ValueError, "earlier cognitive-state version"):
            plan_history.append(earlier_plan)

    def test_evaluation_cross_checks_plan_ids_against_source_cognitive_states(self):
        _, behavioral, evidence = build_fixture([0] * 5)
        cognitive_state = estimate_cognitive_state(behavioral, evidence)
        plan = build_representation_plan(cognitive_state, "ednet_skill:7")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plans.jsonl"
            state_path = root / "states.jsonl"
            plan_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
            state_path.write_text(json.dumps(cognitive_state) + "\n", encoding="utf-8")
            report = evaluate(plan_path, state_path)
        self.assertEqual(report["source_cognitive_state_matches"], 1)
        self.assertEqual(report["source_evidence_reference_matches"], 1)
        self.assertEqual(report["source_diagnostic_recommendation_matches"], 1)
        self.assertEqual(report["source_traceability_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
