from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "trajectory"))

from mcp_ri.cognitive_state import estimate_cognitive_state  # noqa: E402
from mcp_ri.evidence.adapters.interaction import InteractionAdapter  # noqa: E402
from mcp_ri.evidence.adapters.temporal import TemporalHistoryAdapter  # noqa: E402
from mcp_ri.evidence.registry import EvidenceRegistry  # noqa: E402
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator  # noqa: E402
from mcp_ri.representation import (  # noqa: E402
    RepresentationAvailabilityRegistry,
    build_representation_plan,
)
from mcp_ri.trajectory import (  # noqa: E402
    ConceptDependencyRegistry,
    TrajectoryManager,
    build_trajectory,
    detect_diversion,
    validate_diversion,
    validate_trajectory,
)
from mcp_ri.trajectory.transition_rules import validate_transition  # noqa: E402
from trajectory_metrics import evaluate_records, validate_artifacts  # noqa: E402


TARGET = "ednet_skill:12"
SUPPORT = "ednet_skill:34"
TIME = "2026-01-01T00:00:00+00:00"


def phase_states(target_labels: list[int], support_labels: list[int] | None = None,
                 *, conflict: bool = False, conflict_concept: str = TARGET,
                 learner_id: str = "u-phase13"):
    accumulator = LearnerStateAccumulator(learner_id)
    adapter = InteractionAdapter()
    interactions = []
    order = 0
    for concept, labels in ((TARGET, target_labels), (SUPPORT, support_labels or [])):
        tag = concept.split(":", 1)[1]
        for label in labels:
            row = {
                "learner_id": learner_id,
                "source_row_order": str(order),
                "timestamp": str(2_100_000 + order * 1000),
                "question_id": f"q{order}",
                "solving_id": f"s{order}",
                "submitted_answer": "a" if label else "b",
                "correctness": str(label),
                "skill_tags": tag,
                "session_id": "phase13-synthetic-session",
                "is_exact_duplicate": "0",
            }
            interactions.append(adapter.from_processed_row(row))
            accumulator.update(row)
            order += 1
    behavioral = accumulator.snapshot()
    evidence = list(interactions)
    temporal = TemporalHistoryAdapter().from_learner_state(
        behavioral,
        state_reference=f"synthetic-phase13:{learner_id}:{order}",
        related_evidence_ids=[item["evidence_id"] for item in interactions],
    )
    evidence.append(temporal)
    conflicts = []
    if conflict:
        registry = EvidenceRegistry()
        for record in evidence:
            registry.add(record)
        selected = [item for item in interactions
                    if conflict_concept in item["content"].get("skill_ids", [])]
        conflicts = [registry.add_conflict(
            [selected[0]["evidence_id"], selected[1]["evidence_id"]],
            conflict_type="synthetic_disagreement",
            description="Synthetic Phase 13 conflict fixture; not an EdNet observation.",
        )]
        evidence = registry.records
    cognitive = estimate_cognitive_state(behavioral, evidence, conflicts=conflicts)
    return behavioral, cognitive, evidence


def trajectory(*, learner_id: str = "u-phase13", trajectory_id: str = "traj-synthetic",
               previous_plan_id: str | None = "rp-original"):
    return build_trajectory(
        learner_id, TARGET, "Work through the target concept",
        target_skill_ids=[TARGET], learning_objectives=["Explain the target relationship"],
        expected_progression=[
            {"step_id": "step-intro", "concept_id": "ednet_skill:2", "objective": "Recall context", "status": "completed"},
            {"step_id": "step-target", "concept_id": TARGET, "objective": "Explain the target", "status": "current"},
            {"step_id": "step-practice", "concept_id": TARGET, "objective": "Try a related item", "status": "pending"},
        ],
        previous_representation_plan_id=previous_plan_id,
        previous_cognitive_state_id="cs-original",
        supporting_evidence_ids=["ev_previous"],
        previous_interventions=[{"intervention_id": "int-prev", "status": "observed_reference_only"}],
        learning_history_reference="history:synthetic-phase13",
        trajectory_id=trajectory_id,
        created_at=TIME,
    )


def configured_registry(*, status: str = "manually_configured"):
    return ConceptDependencyRegistry([{
        "source_concept_id": SUPPORT,
        "target_concept_id": TARGET,
        "relationship_type": "PREREQUISITE",
        "source": "explicit synthetic test fixture",
        "verification_status": status,
        "confidence": 0.5,
        "created_at": TIME,
    }], created_at=TIME)


def active_manager(*, max_depth: int = 1, max_active: int = 1,
                   learner_id: str = "u-phase13", trajectory_id: str = "traj-synthetic"):
    manager = TrajectoryManager(dependency_registry=configured_registry(),
                                max_diversion_depth=max_depth,
                                max_active_diversions_per_learner=max_active)
    manager.create(trajectory(learner_id=learner_id, trajectory_id=trajectory_id))
    manager.activate(trajectory_id, occurred_at=TIME)
    return manager


class TrajectoryCreationAndStateTests(unittest.TestCase):
    def test_versioned_initial_trajectory_and_activation(self):
        manager = TrajectoryManager()
        created = manager.create(trajectory())
        self.assertEqual((created["trajectory_version"], created["current_status"]), (1, "CREATED"))
        active = manager.activate(created["trajectory_id"], occurred_at=TIME)
        self.assertEqual((active["trajectory_version"], active["current_status"]), (2, "ACTIVE"))
        validate_trajectory(active)

    def test_normal_progression_without_diversion(self):
        behavioral, cognitive, evidence = phase_states([1] * 10, [1] * 10)
        manager = active_manager()
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(result["decision"]["action"], "CONTINUE_PRIMARY")
        self.assertEqual(result["trajectory"]["current_status"], "ACTIVE")
        self.assertFalse(result["created"])

    def test_valid_transition_graph_rejects_arbitrary_edges(self):
        validate_transition("ACTIVE", "PAUSED")
        with self.assertRaisesRegex(ValueError, "invalid trajectory transition"):
            validate_transition("CREATED", "DIVERTED")
        manager = TrajectoryManager()
        manager.create(trajectory())
        with self.assertRaisesRegex(ValueError, "invalid trajectory transition"):
            manager.pause("traj-synthetic", reason="pause", occurred_at=TIME)

    def test_advance_preserves_completed_steps(self):
        manager = active_manager()
        progressed = manager.advance_step("traj-synthetic", evidence_ids=["ev_step"], occurred_at=TIME)
        self.assertEqual(progressed["completed_steps"], ["step-intro", "step-target"])
        self.assertEqual(progressed["current_learning_step"], "step-practice")


class DiversionDetectionTests(unittest.TestCase):
    def test_repeated_incorrect_responses_create_a_bounded_diagnostic_diversion(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 10)
        manager = active_manager()
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertTrue(result["created"])
        self.assertEqual(result["decision"]["rule_id"], "repeated_incorrect_responses")
        self.assertEqual(result["diversion"]["diversion_concept_id"], SUPPORT)
        self.assertIn("does not establish a prerequisite deficit", result["diversion"]["diversion_reason"])

    def test_declining_recent_performance_can_trigger_diversion(self):
        behavioral, cognitive, evidence = phase_states([1] * 5 + [0] * 5, [0] * 10)
        manager = active_manager()
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertTrue(result["created"])
        self.assertIn("declining_recent_performance", result["decision"]["rule_id"])

    def test_missing_dependency_does_not_invent_prerequisite(self):
        behavioral, cognitive, evidence = phase_states([0] * 5)
        manager = TrajectoryManager(dependency_registry=ConceptDependencyRegistry())
        manager.create(trajectory())
        manager.activate("traj-synthetic", occurred_at=TIME)
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(result["decision"]["rule_id"], "no_prerequisite_relationship")
        self.assertEqual(result["trajectory"]["current_status"], "ACTIVE")
        self.assertIsNone(result["diversion"])

    def test_conflicting_evidence_requests_more_information(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [1] * 10, conflict=True)
        manager = active_manager()
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(result["decision"]["rule_id"], "conflicting_evidence")
        self.assertEqual(result["decision"]["action"], "REQUEST_ADDITIONAL_EVIDENCE")
        self.assertIsNone(result["diversion"])
        estimate = next(item for item in cognitive["concept_estimates"] if item["concept_id"] == TARGET)
        self.assertTrue(estimate["contradictory_evidence_ids"])

    def test_insufficient_evidence_preserves_primary_trajectory(self):
        behavioral, cognitive, evidence = phase_states([0] * 4, [1] * 10)
        result = active_manager().evaluate("traj-synthetic", behavioral_state=behavioral,
                                           cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(result["decision"]["rule_id"], "insufficient_current_concept_evidence")
        self.assertFalse(result["created"])

    def test_strong_supporting_concept_evidence_does_not_trigger_a_prerequisite_diversion(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [1] * 10)
        result = active_manager().evaluate("traj-synthetic", behavioral_state=behavioral,
                                           cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(result["decision"]["rule_id"], "supporting_concept_evidence_not_indicative_of_gap")
        self.assertFalse(result["created"])

    def test_synthetic_dependencies_are_excluded_unless_explicitly_enabled(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 5)
        registry = configured_registry(status="synthetic_test")
        manager = TrajectoryManager(dependency_registry=registry)
        manager.create(trajectory())
        manager.activate("traj-synthetic", occurred_at=TIME)
        denied = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(denied["decision"]["rule_id"], "no_prerequisite_relationship")

        manager2 = TrajectoryManager(dependency_registry=registry)
        manager2.create(trajectory(trajectory_id="traj-synth-enabled"))
        manager2.activate("traj-synth-enabled", occurred_at=TIME)
        allowed = manager2.evaluate("traj-synth-enabled", behavioral_state=behavioral,
                                     cognitive_state=cognitive, evidence_records=evidence,
                                     allow_synthetic_dependencies=True, occurred_at=TIME)
        self.assertTrue(allowed["created"])

    def test_unavailable_representation_is_not_interpreted_as_knowledge_gap(self):
        behavioral, cognitive, evidence = phase_states([1] * 10)
        source = trajectory(trajectory_id="traj-for-plan", previous_plan_id=None)
        plan = build_representation_plan(
            cognitive, TARGET,
            behavioral_state=behavioral,
            evidence_records=evidence,
            teaching_context={"trajectory_id": source["trajectory_id"], "current_representation": None},
        )
        self.assertEqual(plan["decision"]["selected_action"], "defer_until_capability_available")
        manager = TrajectoryManager()
        manager.create(source)
        manager.activate(source["trajectory_id"], occurred_at=TIME)
        result = manager.evaluate(source["trajectory_id"], behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence,
                                  representation_plan=plan, occurred_at=TIME)
        self.assertEqual(result["decision"]["rule_id"], "representation_capability_unavailable")
        self.assertEqual(result["trajectory"]["current_status"], "ACTIVE")

    def test_missing_state_and_missing_concept_estimate_request_evidence(self):
        result = detect_diversion(trajectory())
        self.assertEqual(result["rule_id"], "insufficient_state_inputs")
        behavioral, cognitive, evidence = phase_states([1] * 5)
        altered = trajectory()
        altered["current_concept_id"] = "ednet_skill:999"
        altered["expected_progression"][1]["concept_id"] = "ednet_skill:999"
        decision = detect_diversion(altered, behavioral_state=behavioral, cognitive_state=cognitive,
                                    evidence_records=evidence)
        self.assertEqual(decision["rule_id"], "missing_current_concept_estimate")

    def test_phase10_evidence_must_be_referenced_and_learner_matched(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 5)
        invalid = dict(evidence[0])
        invalid["evidence_id"] = "ev_" + "f" * 32
        with self.assertRaisesRegex(ValueError, "referenced by the supplied cognitive state"):
            detect_diversion(trajectory(), behavioral_state=behavioral,
                             cognitive_state=cognitive, evidence_records=[invalid])

    def test_phase9_phase11_statistics_must_agree_before_diversion(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 10)
        mismatched = {**behavioral, "concept_states": [dict(item) for item in behavioral["concept_states"]]}
        mismatched["concept_states"][0]["recent_accuracy"] = 0.5
        with self.assertRaisesRegex(ValueError, "do not match"):
            detect_diversion(trajectory(), behavioral_state=mismatched,
                             cognitive_state=cognitive, evidence_records=evidence)

    def test_insufficient_supporting_evidence_cannot_become_a_diversion(self):
        behavioral, cognitive, evidence = phase_states([0] * 5, [1] * 5)
        cognitive = dict(cognitive)
        cognitive["concept_estimates"] = [dict(item) for item in cognitive["concept_estimates"]]
        target = next(item for item in cognitive["concept_estimates"] if item["concept_id"] == TARGET)
        missing_id = target["supporting_evidence_ids"][0]
        target["supporting_evidence_ids"] = []
        with self.assertRaises(ValueError):
            detect_diversion(trajectory(), behavioral_state=behavioral, cognitive_state=cognitive,
                             evidence_records=evidence)


class DiversionLifecycleTests(unittest.TestCase):
    def make_diversion(self, *, target_labels=None, support_labels=None, manager=None):
        behavioral, cognitive, evidence = phase_states(target_labels or [0] * 5,
                                                        support_labels or [0] * 10)
        manager = manager or active_manager()
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertTrue(result["created"], result["decision"])
        return manager, result, behavioral, cognitive, evidence

    def test_diversion_object_is_versioned_and_parent_linked(self):
        manager, result, _, _, _ = self.make_diversion()
        diversion = result["diversion"]
        validate_diversion(diversion)
        self.assertEqual(diversion["parent_trajectory_id"], "traj-synthetic")
        self.assertEqual(manager.history.parent_trajectory_of_diversion(diversion["diversion_id"]), "traj-synthetic")
        self.assertEqual(result["trajectory"]["orchestration"]["active_diversion_id"], diversion["diversion_id"])

    def test_context_snapshot_preserves_exact_original_step_and_references(self):
        manager, result, _, _, _ = self.make_diversion()
        snapshot = result["context_snapshot"]
        self.assertEqual(snapshot["current_learning_step"], "step-target")
        self.assertEqual(snapshot["completed_steps"], ["step-intro"])
        self.assertEqual(snapshot["pending_steps"], ["step-practice"])
        self.assertEqual(snapshot["previous_representation_plan_id"], "rp-original")
        self.assertEqual(snapshot["previous_cognitive_state_id"], "cs-original")
        self.assertEqual(manager.history.get_context_snapshot(snapshot["context_snapshot_id"]), snapshot)

    def test_diversion_progress_is_append_only_and_duplicate_evaluation_is_idempotent(self):
        manager, result, _, cognitive, evidence = self.make_diversion()
        diversion_id = result["diversion"]["diversion_id"]
        known = {item["evidence_id"] for item in cognitive["evidence_references"]}
        first = manager.record_diversion_progress(diversion_id, cognitive_state=cognitive,
                                                  known_evidence_ids=known, evaluated_at=TIME)
        event_count = len(manager.history.history_for_trajectory("traj-synthetic"))
        second = manager.record_diversion_progress(diversion_id, cognitive_state=cognitive,
                                                   known_evidence_ids=known, evaluated_at=TIME)
        self.assertEqual(first, second)
        self.assertEqual(len(manager.history.history_for_trajectory("traj-synthetic")), event_count)
        self.assertEqual(first["diversion_version"], 2)

    def test_diversion_can_be_revised_without_changing_its_supporting_concept(self):
        manager, result, _, cognitive, _ = self.make_diversion()
        diversion_id = result["diversion"]["diversion_id"]
        revised = manager.revise_diversion(
            diversion_id,
            reason="A second diagnostic prompt is needed before reassessment.",
            new_resume_condition="Collect two distinct diagnostic observations and re-evaluate the preserved parent step.",
            supporting_evidence_ids=cognitive["concept_estimates"][0]["supporting_evidence_ids"],
            cognitive_state_reference={"cognitive_state_id": cognitive["cognitive_state_id"],
                                       "state_version": cognitive["state_version"]},
            occurred_at=TIME,
        )
        self.assertEqual(revised["diversion"]["diversion_version"], 2)
        self.assertEqual(revised["diversion"]["diversion_concept_id"], SUPPORT)
        self.assertFalse(revised["diversion"]["revision_history"][0]["target_concept_changed"])

    def test_progress_evaluation_limit_stops_automatic_diversion_loops(self):
        manager = active_manager()
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 10)
        created = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                   cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        diversion_id = created["diversion"]["diversion_id"]
        for offset in (0, 1, 2):
            _, current, _ = phase_states([0] * 5, [0] * (10 + offset))
            manager.record_diversion_progress(diversion_id, cognitive_state=current,
                                              evaluated_at=f"2026-01-01T00:00:0{offset}+00:00")
        with self.assertRaisesRegex(ValueError, "maximum diversion progress evaluations"):
            _, extra, _ = phase_states([0] * 5, [0] * 13)
            manager.record_diversion_progress(diversion_id, cognitive_state=extra, evaluated_at="2026-01-01T00:00:03+00:00")
        final_state = phase_states([0] * 5, [0] * 12)[1]
        outcome = manager.assess_resumption(diversion_id, cognitive_state=final_state)
        self.assertEqual(outcome["rule_id"], "diversion_scope_limit_reached")
        self.assertEqual(outcome["outcome"], "REQUEST_ADDITIONAL_EVIDENCE")

    def test_unavailable_progress_evidence_reference_is_rejected(self):
        manager, result, _, cognitive, _ = self.make_diversion()
        with self.assertRaisesRegex(ValueError, "unavailable evidence IDs"):
            manager.record_diversion_progress(result["diversion"]["diversion_id"], cognitive_state=cognitive,
                                              known_evidence_ids={"ev_known"}, evaluated_at=TIME)

    def test_one_correct_response_is_not_enough_for_resumption(self):
        manager, result, _, _, _ = self.make_diversion()
        _, sparse_cognitive, sparse_evidence = phase_states([0] * 5, [1])
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], cognitive_state=sparse_cognitive)
        self.assertEqual(outcome["outcome"], "REQUEST_ADDITIONAL_EVIDENCE")
        self.assertFalse(outcome["mastery_claim"])

    def test_successful_resumption_restores_exact_previous_step(self):
        manager, result, _, _, _ = self.make_diversion()
        _, supporting_cognitive, _ = phase_states([0] * 5, [1] * 10)
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], cognitive_state=supporting_cognitive)
        self.assertEqual(outcome["outcome"], "RESUME_ORIGINAL_STEP")
        applied = manager.apply_resumption(result["diversion"]["diversion_id"], outcome, occurred_at=TIME)
        self.assertTrue(applied["changed"])
        self.assertEqual(applied["trajectory"]["current_status"], "ACTIVE")
        self.assertEqual(applied["trajectory"]["current_learning_step"], "step-target")
        self.assertEqual(applied["trajectory"]["completed_steps"], ["step-intro"])
        self.assertEqual(applied["trajectory"]["pending_steps"], ["step-practice"])
        self.assertIsNone(applied["trajectory"]["orchestration"]["active_diversion_id"])
        self.assertEqual(applied["diversion"]["diversion_status"], "RESOLVED")

    def test_resumption_can_use_a_different_available_representation_plan(self):
        manager, result, _, _, _ = self.make_diversion()
        behavioral, cognitive, evidence = phase_states([0] * 5, [1] * 10)
        registry = RepresentationAvailabilityRegistry([{
            "representation_id": "worked_example", "status": "available",
            "provider_id": "synthetic-content-provider", "content_ids": ["synthetic-example-1"],
            "reason": "Synthetic test fixture only.",
        }])
        alternative = build_representation_plan(
            cognitive, TARGET, behavioral_state=behavioral, evidence_records=evidence,
            registry=registry,
            teaching_context={"trajectory_id": "traj-synthetic", "current_representation": "textual"},
        )
        self.assertEqual(alternative["decision"]["selected_representation"], "worked_example")
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"],
                                            cognitive_state=cognitive,
                                            representation_plan=alternative)
        self.assertEqual(outcome["outcome"], "RESUME_WITH_ALTERNATIVE_REPRESENTATION")
        applied = manager.apply_resumption(result["diversion"]["diversion_id"], outcome, occurred_at=TIME)
        self.assertEqual(applied["trajectory"]["context"]["previous_representation_plan_id"], alternative["plan_id"])
        self.assertEqual(applied["trajectory"]["current_learning_step"], "step-target")

    def test_unresolved_supporting_concept_keeps_diversion_open(self):
        manager, result, _, _, _ = self.make_diversion()
        _, weak_cognitive, _ = phase_states([0] * 5, [0] * 10)
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], cognitive_state=weak_cognitive)
        self.assertEqual(outcome["outcome"], "CONTINUE_DIVERSION")
        applied = manager.apply_resumption(result["diversion"]["diversion_id"], outcome, occurred_at=TIME)
        self.assertFalse(applied["changed"])
        self.assertEqual(applied["trajectory"]["current_status"], "DIVERTED")
        self.assertEqual(applied["diversion"]["diversion_status"], "ACTIVE")

    def test_conflicting_supporting_evidence_cannot_close_diversion(self):
        manager, result, _, _, _ = self.make_diversion()
        _, conflict_cognitive, _ = phase_states([0] * 5, [1] * 10, conflict=True, conflict_concept=SUPPORT)
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], cognitive_state=conflict_cognitive)
        self.assertEqual(outcome["outcome"], "REQUEST_ADDITIONAL_EVIDENCE")
        self.assertIn("Contradictory", outcome["explanation"])

    def test_replanning_closes_diversion_and_retains_previous_version(self):
        manager, result, _, _, _ = self.make_diversion()
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], replan_requested=True)
        applied = manager.apply_resumption(result["diversion"]["diversion_id"], outcome,
                                           new_target_concept_id="ednet_skill:88",
                                           new_learning_goal="Replan the parent goal", occurred_at=TIME)
        self.assertEqual(applied["trajectory"]["current_status"], "REPLANNED")
        self.assertEqual(applied["trajectory"]["target_concept_id"], "ednet_skill:88")
        self.assertEqual(manager.history.reconstruct("traj-synthetic", 2)["target_concept_id"], TARGET)
        self.assertEqual(applied["diversion"]["diversion_status"], "CLOSED")

    def test_parent_completion_is_an_explicit_workflow_decision(self):
        manager, result, _, _, _ = self.make_diversion()
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], completion_requested=True)
        applied = manager.apply_resumption(result["diversion"]["diversion_id"], outcome, occurred_at=TIME)
        self.assertEqual(applied["trajectory"]["current_status"], "COMPLETED")
        self.assertFalse(outcome["mastery_claim"])


class HistoryAndBoundTests(unittest.TestCase):
    def test_maximum_depth_is_enforced(self):
        manager = TrajectoryManager(dependency_registry=configured_registry(), max_diversion_depth=1)
        initial = trajectory()
        initial["orchestration"]["current_depth"] = 1
        manager.create(initial)
        manager.activate("traj-synthetic", occurred_at=TIME)
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 5)
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(result["decision"]["rule_id"], "maximum_diversion_depth_reached")
        self.assertFalse(result["created"])

    def test_only_one_active_diversion_per_learner(self):
        manager = active_manager(max_active=1)
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 5)
        first = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                 cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        second_trajectory = trajectory(trajectory_id="traj-second")
        second_trajectory["learner_id"] = "u-phase13"
        manager.create(second_trajectory)
        manager.activate("traj-second", occurred_at=TIME)
        second = manager.evaluate("traj-second", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertTrue(first["created"])
        self.assertEqual(second["decision"]["rule_id"], "maximum_active_diversions_per_learner_reached")
        self.assertFalse(second["created"])

    def test_repeated_declined_evaluation_does_not_append_duplicate_history(self):
        behavioral, cognitive, evidence = phase_states([1] * 5)
        manager = TrajectoryManager()
        manager.create(trajectory())
        manager.activate("traj-synthetic", occurred_at=TIME)
        first = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                 cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        count = len(manager.history.history_for_trajectory("traj-synthetic"))
        second = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        self.assertEqual(first["event"]["event_id"], second["event"]["event_id"])
        self.assertEqual(count, len(manager.history.history_for_trajectory("traj-synthetic")))

    def test_historical_reconstruction_and_transition_inspection(self):
        manager = active_manager()
        original = manager.history.reconstruct("traj-synthetic", 1)
        active = manager.history.reconstruct("traj-synthetic", 2)
        event = manager.history.history_for_trajectory("traj-synthetic")[-1]
        self.assertEqual(original["current_status"], "CREATED")
        self.assertEqual(active["current_status"], "ACTIVE")
        self.assertEqual(manager.history.inspect_transition(event["event_id"]), event)

    def test_manager_can_resume_from_the_latest_exported_history_snapshot(self):
        manager = active_manager()
        restored_manager = TrajectoryManager(history=manager.history)
        restored = restored_manager.restore("traj-synthetic")
        self.assertEqual(restored, manager.latest("traj-synthetic"))
        paused = restored_manager.pause("traj-synthetic", reason="Restored-history pause", occurred_at=TIME)
        self.assertEqual(paused["current_status"], "PAUSED")
        self.assertEqual(manager.history.reconstruct("traj-synthetic")["current_status"], "PAUSED")

    def test_history_returns_copies_and_cannot_overwrite_prior_versions(self):
        manager = active_manager()
        fetched = manager.latest("traj-synthetic")
        fetched["primary_learning_goal"] = "tampered"
        self.assertNotEqual(manager.latest("traj-synthetic")["primary_learning_goal"], "tampered")
        events = manager.history.history_for_trajectory("traj-synthetic")
        last = events[-1]
        tampered_snapshot = dict(last["trajectory_snapshot"])
        tampered_snapshot["primary_learning_goal"] = "tampered"
        with self.assertRaisesRegex(ValueError, "same-version history events cannot mutate"):
            manager.history.append_event({**last, "event_id": "tampered-event",
                                          "previous_event_id": last["event_id"],
                                          "trajectory_snapshot": tampered_snapshot})

    def test_history_diversion_snapshot_link_is_valid(self):
        manager, result, _, _, _ = DiversionLifecycleTests().make_diversion()
        self.assertEqual(manager.history.parent_trajectory_of_diversion(result["diversion"]["diversion_id"]),
                         result["trajectory"]["trajectory_id"])
        self.assertEqual(manager.history.get_context_snapshot(result["diversion"]["context_snapshot_id"])["parent_trajectory_id"],
                         result["trajectory"]["trajectory_id"])

    def test_dependency_registry_default_empty_and_provenance_labels(self):
        registry = ConceptDependencyRegistry()
        self.assertEqual(registry.as_dict()["dependencies"], [])
        item = configured_registry().as_dict()["dependencies"][0]
        self.assertEqual(item["verification_status"], "manually_configured")
        self.assertNotEqual(item["source"], "EdNet observation")

    def test_prerequisite_registry_rejects_cycles(self):
        registry = ConceptDependencyRegistry()
        registry.add("concept:a", "concept:b", "PREREQUISITE", "manual curriculum review",
                     "manually_configured", created_at=TIME)
        registry.add("concept:b", "concept:c", "PREREQUISITE", "manual curriculum review",
                     "manually_configured", created_at=TIME)
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            registry.add("concept:c", "concept:a", "PREREQUISITE", "manual curriculum review",
                         "manually_configured", created_at=TIME)

    def test_metrics_validate_a_positive_diversion_and_context_export(self):
        manager = active_manager()
        behavioral, cognitive, evidence = phase_states([0] * 5, [0] * 10)
        result = manager.evaluate("traj-synthetic", behavioral_state=behavioral,
                                  cognitive_state=cognitive, evidence_records=evidence, occurred_at=TIME)
        records = {
            "trajectories": [manager.history.reconstruct("traj-synthetic")],
            "diversions": manager.history.diversion_versions,
            "contexts": manager.history.context_snapshots,
            "events": manager.history.events,
            "decisions": [{"cognitive_state_id": cognitive["cognitive_state_id"],
                           "decision": result["decision"], "deterministic_replay_match": True}],
        }
        metrics = evaluate_records(
            manager.history, records,
            {cognitive["cognitive_state_id"]: cognitive},
            max_diversion_depth=1,
        )
        self.assertEqual(metrics["context_preservation_rate_percent"], 100.0)
        self.assertEqual(metrics["parent_child_relationship_validity_percent"], 100.0)
        self.assertEqual(metrics["maximum_depth_enforcement_percent"], 100.0)
        self.assertEqual(metrics["evidence_reference_validity_percent"], 100.0)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for name, values in (
                ("trajectories.jsonl", records["trajectories"]),
                ("diversions.jsonl", records["diversions"]),
                ("context_snapshots.jsonl", records["contexts"]),
                ("history_events.jsonl", records["events"]),
                ("decisions.jsonl", records["decisions"]),
            ):
                (output / name).write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")
            (output / "dependency_registry.json").write_text(
                json.dumps(manager.dependency_registry.as_dict()), encoding="utf-8")
            validated_history, validated_records = validate_artifacts(output)
            self.assertEqual(len(validated_records["contexts"]), 1)
            self.assertEqual(validated_history.parent_trajectory_of_diversion(result["diversion"]["diversion_id"]),
                             "traj-synthetic")

    def test_pausing_and_reactivating_keeps_an_active_diversion_attached(self):
        manager, result, _, _, _ = DiversionLifecycleTests().make_diversion()
        paused = manager.pause("traj-synthetic", reason="Learner pause during support review", occurred_at=TIME)
        self.assertEqual(paused["current_status"], "PAUSED")
        resumed = manager.activate("traj-synthetic", occurred_at=TIME)
        self.assertEqual(resumed["current_status"], "DIVERTED")
        self.assertEqual(resumed["orchestration"]["active_diversion_id"], result["diversion"]["diversion_id"])

    def test_invalid_replan_request_fails_before_mutating_history(self):
        manager, result, _, _, _ = DiversionLifecycleTests().make_diversion()
        outcome = manager.assess_resumption(result["diversion"]["diversion_id"], replan_requested=True)
        before_events = manager.history.history_for_trajectory("traj-synthetic")
        with self.assertRaisesRegex(ValueError, "new target concept and learning goal"):
            manager.apply_resumption(result["diversion"]["diversion_id"], outcome, occurred_at=TIME)
        self.assertEqual(manager.latest("traj-synthetic")["current_status"], "DIVERTED")
        self.assertEqual(manager.history.history_for_trajectory("traj-synthetic"), before_events)


if __name__ == "__main__":
    unittest.main()
