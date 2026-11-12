"""Stateful orchestration facade over immutable trajectory and diversion history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .context_preserver import create_context_snapshot, restore_context
from .dependency_registry import ConceptDependencyRegistry
from .diversion_detector import detect_diversion
from .diversion_manager import close_diversion, create_diversion_record, update_diversion_progress
from .history import TrajectoryHistory
from .models import copy_record, stable_id
from .resumption_engine import evaluate_resumption
from .transition_rules import transition_record
from .validator import validate_diversion, validate_trajectory


class TrajectoryManager:
    """Manage a learner path while preserving each version in `TrajectoryHistory`."""

    def __init__(self, *, history: TrajectoryHistory | None = None,
                 dependency_registry: ConceptDependencyRegistry | None = None,
                 max_diversion_depth: int = 1,
                 max_active_diversions_per_learner: int = 1,
                 max_diversion_evaluations: int = 3) -> None:
        if max_diversion_depth < 1 or max_active_diversions_per_learner < 1 or max_diversion_evaluations < 1:
            raise ValueError("diversion limits must be positive")
        self.history = history or TrajectoryHistory()
        self.dependency_registry = dependency_registry or ConceptDependencyRegistry()
        self.max_diversion_depth = int(max_diversion_depth)
        self.max_active_diversions_per_learner = int(max_active_diversions_per_learner)
        self.max_diversion_evaluations = int(max_diversion_evaluations)
        self._latest: dict[str, dict[str, Any]] = {}

    def create(self, trajectory: Mapping[str, Any]) -> dict[str, Any]:
        candidate = copy_record(trajectory)
        validate_trajectory(candidate)
        if candidate["current_status"] != "CREATED" or candidate["trajectory_version"] != 1:
            raise ValueError("a new trajectory must begin in CREATED at version 1")
        trajectory_id = candidate["trajectory_id"]
        if trajectory_id in self._latest:
            raise ValueError("trajectory already registered")
        self._latest[trajectory_id] = candidate
        event = self.history.build_event(
            trajectory=candidate, event_type="TRAJECTORY_CREATED", occurred_at=candidate["created_at"],
            previous_state=None, trigger="trajectory_created", supporting_evidence_ids=candidate["context"]["supporting_evidence_ids"],
            cognitive_state_reference=self._cognitive_ref(candidate),
            representation_plan_reference=self._plan_ref(candidate), related_diversion_id=None,
            decision_explanation="A primary learning trajectory was created with an explicit target and preserved references.",
        )
        self.history.append_event(event)
        return copy_record(candidate)

    def latest(self, trajectory_id: str) -> dict[str, Any]:
        if trajectory_id not in self._latest:
            raise KeyError(trajectory_id)
        return copy_record(self._latest[trajectory_id])

    def restore(self, trajectory_id: str) -> dict[str, Any]:
        """Attach the latest reconstructed snapshot to continue a history."""
        if trajectory_id in self._latest:
            raise ValueError("trajectory is already attached to this manager")
        trajectory = self.history.reconstruct(trajectory_id)
        validate_trajectory(trajectory)
        self._latest[trajectory_id] = copy_record(trajectory)
        return copy_record(trajectory)

    def activate(self, trajectory_id: str, *, occurred_at: str | None = None) -> dict[str, Any]:
        current = self.latest(trajectory_id)
        target_state = "DIVERTED" if (current["current_status"] == "PAUSED"
                                       and current["orchestration"]["active_diversion_id"] is not None) else "ACTIVE"
        return self._transition(trajectory_id, target_state, "activate_primary_trajectory",
                                 "The primary trajectory or its preserved active diversion resumed.",
                                 occurred_at=occurred_at)

    def pause(self, trajectory_id: str, *, reason: str,
              evidence_ids: list[str] = (), occurred_at: str | None = None) -> dict[str, Any]:
        if not reason.strip():
            raise ValueError("pause reason is required")
        return self._transition(trajectory_id, "PAUSED", "pause", reason, evidence_ids=evidence_ids, occurred_at=occurred_at)

    def advance_step(self, trajectory_id: str, *, evidence_ids: list[str] = (),
                     occurred_at: str | None = None) -> dict[str, Any]:
        current = self.latest(trajectory_id)
        if current["current_status"] != "ACTIVE":
            raise ValueError("only an active primary trajectory can advance")
        progression = current["expected_progression"]
        at_index = next(i for i, step in enumerate(progression) if step["step_id"] == current["current_learning_step"])
        progression[at_index]["status"] = "completed"
        current["completed_steps"] = [step["step_id"] for step in progression if step["status"] == "completed"]
        pending = [step for step in progression if step["status"] == "pending"]
        if not pending:
            return self._commit_update(current, event_type="PROGRESS_UPDATED", trigger="final_learning_step_completed",
                                       explanation="The final configured step was recorded as complete.", evidence_ids=evidence_ids,
                                       new_state="COMPLETED", occurred_at=occurred_at)
        next_step = pending[0]
        next_step["status"] = "current"
        current["current_learning_step"] = next_step["step_id"]
        current["current_concept_id"] = next_step["concept_id"]
        current["pending_steps"] = [step["step_id"] for step in progression if step["status"] == "pending"]
        return self._commit_update(current, event_type="PROGRESS_UPDATED", trigger="learning_step_advanced",
                                   explanation="Completed-step history was retained and the next configured step became current.",
                                   evidence_ids=evidence_ids, occurred_at=occurred_at)

    def evaluate(self, trajectory_id: str, *, behavioral_state: Mapping[str, Any] | None = None,
                 cognitive_state: Mapping[str, Any] | None = None,
                 evidence_records: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]] = (),
                 representation_plan: Mapping[str, Any] | None = None,
                 occurred_at: str | None = None,
                 allow_synthetic_dependencies: bool = False) -> dict[str, Any]:
        trajectory = self.latest(trajectory_id)
        if trajectory["current_status"] != "ACTIVE":
            raise ValueError("diversion evaluation requires an ACTIVE primary trajectory")
        decision = detect_diversion(
            trajectory, behavioral_state=behavioral_state, cognitive_state=cognitive_state,
            evidence_records=evidence_records, representation_plan=representation_plan,
            dependency_registry=self.dependency_registry,
            allow_synthetic_dependencies=allow_synthetic_dependencies,
        )
        now = occurred_at or datetime.now(timezone.utc).isoformat()
        if decision["action"] != "CREATE_DIVERSION":
            previous = self._same_decision_event(trajectory_id, "EVALUATION_DECLINED", decision)
            if previous:
                return {"decision": decision, "trajectory": trajectory, "diversion": None,
                        "event": previous, "created": False}
            event = self._append_same_state_event(
                trajectory, "EVALUATION_DECLINED", decision["rule_id"], decision["explanation"],
                decision["supporting_evidence_ids"], decision["cognitive_state_reference"],
                decision["representation_plan_reference"], now,
            )
            return {"decision": decision, "trajectory": trajectory, "diversion": None,
                    "event": event, "created": False}

        rejection = self._diversion_limit_reason(trajectory, decision)
        if rejection:
            declined = dict(decision)
            declined.update({"action": "REQUEST_ADDITIONAL_EVIDENCE", "rule_id": rejection,
                             "explanation": f"{decision['explanation']} Diversion was not created: {rejection.replace('_', ' ')}; retain the primary path."})
            previous = self._same_decision_event(trajectory_id, "EVALUATION_DECLINED", declined)
            event = previous or self._append_same_state_event(
                trajectory, "EVALUATION_DECLINED", declined["rule_id"], declined["explanation"],
                declined["supporting_evidence_ids"], declined["cognitive_state_reference"],
                declined["representation_plan_reference"], now,
            )
            return {"decision": declined, "trajectory": trajectory, "diversion": None,
                    "event": event, "created": False}

        snapshot = create_context_snapshot(
            trajectory, reason=decision["explanation"],
            supporting_evidence_ids=decision["supporting_evidence_ids"],
            diagnostic_recommendation_ids=self._diagnostic_ids(cognitive_state),
            existing_active_diversion_ids=[item["diversion_id"] for item in self.history.diversions_for_trajectory(trajectory_id)
                                           if item["diversion_status"] == "ACTIVE"],
            created_at=now,
        )
        self.history.append_context_snapshot(snapshot)
        diversion = create_diversion_record(trajectory, decision, snapshot, now=now)
        self.history.append_diversion(diversion)
        previous_state = trajectory["current_status"]
        updated = copy_record(trajectory)
        transition_record(updated, "DIVERTED")
        updated["orchestration"]["active_diversion_id"] = diversion["diversion_id"]
        updated["orchestration"]["current_depth"] = trajectory["orchestration"]["current_depth"] + 1
        updated["trajectory_version"] += 1
        updated["updated_at"] = now
        validate_trajectory(updated)
        event = self._append_transition_event(
            updated, "DIVERSION_CREATED", previous_state, decision["rule_id"],
            decision["explanation"], decision["supporting_evidence_ids"],
            decision["cognitive_state_reference"], decision["representation_plan_reference"],
            diversion["diversion_id"], now,
        )
        self._latest[trajectory_id] = updated
        return {"decision": decision, "trajectory": copy_record(updated),
                "diversion": diversion, "context_snapshot": snapshot, "event": event, "created": True}

    def record_diversion_progress(self, diversion_id: str, *,
                                  behavioral_state: Mapping[str, Any] | None = None,
                                  cognitive_state: Mapping[str, Any] | None = None,
                                  evidence_ids: list[str] | None = None,
                                  known_evidence_ids: set[str] | None = None,
                                  evaluated_at: str | None = None, note: str = "") -> dict[str, Any]:
        diversion = self.history.latest_diversion(diversion_id)
        updated = update_diversion_progress(
            diversion, behavioral_state=behavioral_state, cognitive_state=cognitive_state,
            evidence_ids=evidence_ids, known_evidence_ids=known_evidence_ids,
            evaluated_at=evaluated_at, note=note,
        )
        if updated == diversion:
            return updated
        if len(diversion["progress_history"]) >= self.max_diversion_evaluations:
            raise ValueError("maximum diversion progress evaluations reached; close or replan before adding more")
        self.history.append_diversion(updated)
        trajectory = self.latest(diversion["parent_trajectory_id"])
        event = self.history.build_event(
            trajectory=trajectory, event_type="DIVERSION_PROGRESS", occurred_at=updated["last_evaluated_at"],
            previous_state=trajectory["current_status"], trigger="diversion_progress_updated",
            supporting_evidence_ids=updated["progress_history"][-1]["evidence_ids"],
            cognitive_state_reference=updated["progress_history"][-1]["cognitive_state_reference"],
            representation_plan_reference=diversion["representation_plan_reference"],
            related_diversion_id=diversion_id,
            decision_explanation="A new immutable progress evaluation was attached to the active diversion.",
        )
        self.history.append_event(event)
        return updated

    def revise_diversion(self, diversion_id: str, *, reason: str, new_resume_condition: str,
                         supporting_evidence_ids: list[str] = (),
                         cognitive_state_reference: Mapping[str, Any] | None = None,
                         occurred_at: str | None = None) -> dict[str, Any]:
        diversion = self.history.latest_diversion(diversion_id)
        if diversion["diversion_status"] != "ACTIVE":
            raise ValueError("only an active diversion can be revised")
        if not reason.strip() or not new_resume_condition.strip():
            raise ValueError("revision reason and new resume condition are required")
        now = occurred_at or datetime.now(timezone.utc).isoformat()
        updated = copy_record(diversion)
        updated["diversion_version"] += 1
        updated["updated_at"] = now
        prior_condition = updated["resume_condition"]
        updated["resume_condition"] = new_resume_condition.strip()
        updated["diversion_reason"] = reason.strip()
        updated["supporting_evidence_ids"] = sorted(set(
            updated["supporting_evidence_ids"] + supporting_evidence_ids
        ))
        updated["revision_history"].append({
            "diversion_version": updated["diversion_version"],
            "revised_at": now,
            "reason": reason.strip(),
            "previous_resume_condition": prior_condition,
            "new_resume_condition": new_resume_condition.strip(),
            "supporting_evidence_ids": sorted(set(supporting_evidence_ids)),
            "cognitive_state_reference": copy_record(cognitive_state_reference),
            "target_concept_changed": False,
        })
        validate_diversion(updated)
        self.history.append_diversion(updated)
        trajectory = self.latest(diversion["parent_trajectory_id"])
        event = self._append_same_state_event(
            trajectory, "DIVERSION_REVISED", "diversion_revision", reason.strip(),
            supporting_evidence_ids, cognitive_state_reference,
            diversion["representation_plan_reference"], now, diversion_id,
        )
        return {"diversion": updated, "event": event}

    def assess_resumption(self, diversion_id: str, *, behavioral_state: Mapping[str, Any] | None = None,
                          cognitive_state: Mapping[str, Any] | None = None,
                          representation_plan: Mapping[str, Any] | None = None,
                          replan_requested: bool = False, completion_requested: bool = False) -> dict[str, Any]:
        diversion = self.history.latest_diversion(diversion_id)
        trajectory = self.latest(diversion["parent_trajectory_id"])
        snapshot = self.history.get_context_snapshot(diversion["context_snapshot_id"])
        outcome = evaluate_resumption(
            trajectory, diversion, snapshot, behavioral_state=behavioral_state,
            cognitive_state=cognitive_state, representation_plan=representation_plan,
            replan_requested=replan_requested, completion_requested=completion_requested,
        )
        if (len(diversion["progress_history"]) >= self.max_diversion_evaluations
                and outcome["outcome"] in {"CONTINUE_DIVERSION", "REQUEST_ADDITIONAL_EVIDENCE"}):
            return {
                "outcome": "REQUEST_ADDITIONAL_EVIDENCE",
                "rule_id": "diversion_scope_limit_reached",
                "supporting_evidence_ids": [],
                "representation_plan_reference": None,
                "cognitive_state_reference": None,
                "explanation": "The configured diversion evaluation limit was reached without a resumption decision. Stop automatic continuation and request an explicit human decision to close or replan.",
                "mastery_claim": False,
            }
        return outcome

    def apply_resumption(self, diversion_id: str, outcome: Mapping[str, Any], *,
                         occurred_at: str | None = None,
                         new_target_concept_id: str | None = None,
                         new_learning_goal: str | None = None) -> dict[str, Any]:
        diversion = self.history.latest_diversion(diversion_id)
        trajectory = self.latest(diversion["parent_trajectory_id"])
        snapshot = self.history.get_context_snapshot(diversion["context_snapshot_id"])
        if outcome.get("outcome") not in {
            "RESUME_ORIGINAL_STEP", "RESUME_WITH_ALTERNATIVE_REPRESENTATION", "CONTINUE_DIVERSION",
            "REQUEST_ADDITIONAL_EVIDENCE", "REPLAN_PARENT_TRAJECTORY", "MARK_TRAJECTORY_COMPLETED",
        }:
            raise ValueError("unsupported resumption outcome")
        now = occurred_at or datetime.now(timezone.utc).isoformat()
        previous = self._same_outcome_event(trajectory["trajectory_id"], diversion_id, outcome)
        if previous:
            return {"trajectory": trajectory, "diversion": diversion, "event": previous, "changed": False}
        if (trajectory["current_status"] != "DIVERTED"
                or trajectory["orchestration"]["active_diversion_id"] != diversion_id
                or diversion["diversion_status"] != "ACTIVE"):
            raise ValueError("resumption application requires this active diversion on its diverted parent")
        if (outcome["outcome"] == "REPLAN_PARENT_TRAJECTORY"
                and (not new_target_concept_id or not new_learning_goal)):
            raise ValueError("parent replanning requires a new target concept and learning goal")
        decision_event = self._append_same_state_event(
            trajectory, "RESUMPTION_DECIDED", f"{outcome['outcome']}:{outcome['rule_id']}",
            outcome["explanation"], outcome.get("supporting_evidence_ids", []),
            outcome.get("cognitive_state_reference"), outcome.get("representation_plan_reference"),
            now, diversion_id,
        )
        if outcome["outcome"] in {"CONTINUE_DIVERSION", "REQUEST_ADDITIONAL_EVIDENCE"}:
            return {"trajectory": trajectory, "diversion": diversion, "event": decision_event, "changed": False}

        self._transition(trajectory["trajectory_id"], "RESUMING", outcome["rule_id"],
                         outcome["explanation"], evidence_ids=outcome.get("supporting_evidence_ids", []),
                         related_diversion_id=diversion_id, occurred_at=now,
                         cognitive_state_reference=outcome.get("cognitive_state_reference"),
                         representation_plan_reference=outcome.get("representation_plan_reference"))

        terminal_outcome = outcome["outcome"]
        if terminal_outcome == "REPLAN_PARENT_TRAJECTORY":
            closed = close_diversion(diversion, status="CLOSED", reason="Parent trajectory replanned after diversion review.", resolved_at=now)
            self.history.append_diversion(closed)
            self._append_closure_event(trajectory["trajectory_id"], closed, outcome, now)
            replanned = self.latest(trajectory["trajectory_id"])
            replanned["target_concept_id"] = new_target_concept_id
            replanned["current_concept_id"] = new_target_concept_id
            replanned["primary_learning_goal"] = new_learning_goal
            replanned["learning_objectives"] = []
            new_step = {"step_id": f"step:{new_target_concept_id}:1", "concept_id": new_target_concept_id,
                        "objective": new_learning_goal, "status": "current"}
            replanned["expected_progression"] = [new_step]
            replanned["current_learning_step"] = new_step["step_id"]
            replanned["completed_steps"] = []
            replanned["pending_steps"] = []
            replanned["orchestration"]["active_diversion_id"] = None
            replanned["orchestration"]["current_depth"] = snapshot["original_current_depth"]
            self._apply_outcome_references(replanned, outcome)
            self._latest[trajectory["trajectory_id"]] = replanned
            final = self._transition(trajectory["trajectory_id"], "REPLANNED", "parent_replanned",
                                     "Parent objective and progression were replaced in a new immutable trajectory version.",
                                     evidence_ids=outcome.get("supporting_evidence_ids", []),
                                     related_diversion_id=diversion_id, occurred_at=now,
                                     cognitive_state_reference=outcome.get("cognitive_state_reference"),
                                     representation_plan_reference=outcome.get("representation_plan_reference"))
            return {"trajectory": final, "diversion": closed,
                    "context_restored": restore_context(final, snapshot), "changed": True}

        if terminal_outcome == "MARK_TRAJECTORY_COMPLETED":
            closed = close_diversion(diversion, status="CLOSED", reason="Parent trajectory was explicitly marked complete.", resolved_at=now)
            self.history.append_diversion(closed)
            self._append_closure_event(trajectory["trajectory_id"], closed, outcome, now)
            completed = self.latest(trajectory["trajectory_id"])
            completed["orchestration"]["active_diversion_id"] = None
            completed["orchestration"]["current_depth"] = snapshot["original_current_depth"]
            self._apply_outcome_references(completed, outcome)
            self._latest[trajectory["trajectory_id"]] = completed
            final = self._transition(trajectory["trajectory_id"], "COMPLETED", "parent_completed",
                                     outcome["explanation"], evidence_ids=outcome.get("supporting_evidence_ids", []),
                                     related_diversion_id=diversion_id, occurred_at=now,
                                     cognitive_state_reference=outcome.get("cognitive_state_reference"),
                                     representation_plan_reference=outcome.get("representation_plan_reference"))
            return {"trajectory": final, "diversion": closed, "context_restored": restore_context(final, snapshot), "changed": True}

        closed = close_diversion(diversion, status="RESOLVED", reason=outcome["explanation"], resolved_at=now)
        self.history.append_diversion(closed)
        self._append_closure_event(trajectory["trajectory_id"], closed, outcome, now)
        resumed = self.latest(trajectory["trajectory_id"])
        restored = restore_context(resumed, snapshot)
        if terminal_outcome == "RESUME_WITH_ALTERNATIVE_REPRESENTATION":
            plan_ref = outcome.get("representation_plan_reference") or {}
            resumed["context"]["previous_representation_plan_id"] = plan_ref.get("plan_id")
        resumed["current_concept_id"] = restored["target_concept_id"]
        resumed["current_learning_step"] = restored["current_learning_step"]
        resumed["completed_steps"] = restored["completed_steps"]
        resumed["pending_steps"] = restored["pending_steps"]
        resumed["primary_learning_goal"] = restored["primary_learning_goal"]
        resumed["orchestration"]["active_diversion_id"] = None
        resumed["orchestration"]["current_depth"] = restored["current_depth"]
        self._apply_outcome_references(resumed, outcome)
        self._latest[trajectory["trajectory_id"]] = resumed
        final = self._transition(trajectory["trajectory_id"], "ACTIVE", "parent_resumed",
                                 outcome["explanation"], evidence_ids=outcome.get("supporting_evidence_ids", []),
                                 related_diversion_id=diversion_id, occurred_at=now,
                                 cognitive_state_reference=outcome.get("cognitive_state_reference"),
                                 representation_plan_reference=outcome.get("representation_plan_reference"))
        return {"trajectory": final, "diversion": closed, "context_restored": restored, "changed": True}

    def replan(self, trajectory_id: str, *, target_concept_id: str, learning_goal: str,
               reason: str, evidence_ids: list[str] = (), occurred_at: str | None = None) -> dict[str, Any]:
        trajectory = self.latest(trajectory_id)
        if trajectory["current_status"] != "ACTIVE":
            raise ValueError("direct replanning requires an active primary trajectory")
        if not target_concept_id or not learning_goal.strip() or not reason.strip():
            raise ValueError("new target, goal and replanning reason are required")
        now = occurred_at or datetime.now(timezone.utc).isoformat()
        updated = copy_record(trajectory)
        updated["target_concept_id"] = target_concept_id
        updated["current_concept_id"] = target_concept_id
        updated["primary_learning_goal"] = learning_goal.strip()
        updated["learning_objectives"] = []
        step = {"step_id": f"step:{target_concept_id}:1", "concept_id": target_concept_id,
                "objective": learning_goal.strip(), "status": "current"}
        updated["expected_progression"] = [step]
        updated["current_learning_step"] = step["step_id"]
        updated["completed_steps"] = []
        updated["pending_steps"] = []
        return self._commit_update(updated, event_type="REPLANNED", trigger="parent_replanned",
                                   explanation=reason, evidence_ids=evidence_ids,
                                   new_state="REPLANNED", occurred_at=now)

    def _diversion_limit_reason(self, trajectory: Mapping[str, Any], decision: Mapping[str, Any]) -> str | None:
        if trajectory["orchestration"]["current_depth"] >= self.max_diversion_depth:
            return "maximum_diversion_depth_reached"
        if trajectory["orchestration"]["active_diversion_id"] is not None:
            return "active_diversion_already_exists"
        if any(item["learner_id"] == trajectory["learner_id"] and item["diversion_status"] == "ACTIVE"
               for item in self.history.diversions_for_trajectory(trajectory["trajectory_id"])):
            return "duplicate_active_diversion"
        active_for_learner = [item for item in self.history.all_diversions()
                              if item["learner_id"] == trajectory["learner_id"] and item["diversion_status"] == "ACTIVE"]
        if len(active_for_learner) >= self.max_active_diversions_per_learner:
            return "maximum_active_diversions_per_learner_reached"
        if any(item["parent_trajectory_id"] == trajectory["trajectory_id"]
               and item["diversion_concept_id"] == decision["target_concept_id"]
               and item["diversion_status"] == "ACTIVE"
               for item in self.history.diversions_for_trajectory(trajectory["trajectory_id"])):
            return "duplicate_active_diversion_for_target"
        return None

    def _transition(self, trajectory_id: str, new_state: str, trigger: str, explanation: str,
                    *, evidence_ids: list[str] = (), related_diversion_id: str | None = None,
                    occurred_at: str | None = None,
                    cognitive_state_reference: Mapping[str, Any] | None = None,
                    representation_plan_reference: Mapping[str, Any] | None = None) -> dict[str, Any]:
        trajectory = self.latest(trajectory_id)
        updated = copy_record(trajectory)
        old_state = updated["current_status"]
        transition_record(updated, new_state)
        now = occurred_at or datetime.now(timezone.utc).isoformat()
        updated["trajectory_version"] += 1
        updated["updated_at"] = now
        validate_trajectory(updated)
        self._append_transition_event(updated, "STATE_TRANSITION", old_state, trigger, explanation,
                                      evidence_ids, cognitive_state_reference or self._cognitive_ref(updated),
                                      representation_plan_reference or self._plan_ref(updated),
                                      related_diversion_id, now)
        self._latest[trajectory_id] = updated
        return copy_record(updated)

    def _commit_update(self, trajectory: dict[str, Any], *, event_type: str, trigger: str,
                       explanation: str, evidence_ids: list[str], new_state: str | None = None,
                       occurred_at: str | None = None) -> dict[str, Any]:
        trajectory_id = trajectory["trajectory_id"]
        prior = self.latest(trajectory_id)
        old_state = prior["current_status"]
        if new_state is not None:
            transition_record(trajectory, new_state)
        now = occurred_at or datetime.now(timezone.utc).isoformat()
        trajectory["trajectory_version"] = prior["trajectory_version"] + 1
        trajectory["updated_at"] = now
        validate_trajectory(trajectory)
        self._append_transition_event(trajectory, event_type, old_state, trigger, explanation,
                                      evidence_ids, self._cognitive_ref(trajectory),
                                      self._plan_ref(trajectory), None, now)
        self._latest[trajectory_id] = copy_record(trajectory)
        return copy_record(trajectory)

    def _append_transition_event(self, trajectory: Mapping[str, Any], event_type: str,
                                 previous_state: str | None, trigger: str, explanation: str,
                                 evidence_ids: list[str], cognitive_ref: Mapping[str, Any] | None,
                                 plan_ref: Mapping[str, Any] | None, diversion_id: str | None,
                                 now: str) -> dict[str, Any]:
        event = self.history.build_event(
            trajectory=trajectory, event_type=event_type, occurred_at=now,
            previous_state=previous_state, trigger=trigger, supporting_evidence_ids=evidence_ids,
            cognitive_state_reference=cognitive_ref, representation_plan_reference=plan_ref,
            related_diversion_id=diversion_id, decision_explanation=explanation,
        )
        return self.history.append_event(event)

    def _append_same_state_event(self, trajectory: Mapping[str, Any], event_type: str,
                                 trigger: str, explanation: str, evidence_ids: list[str],
                                 cognitive_ref: Mapping[str, Any] | None,
                                 plan_ref: Mapping[str, Any] | None, now: str,
                                 diversion_id: str | None = None) -> dict[str, Any]:
        return self._append_transition_event(trajectory, event_type, trajectory["current_status"],
                                             trigger, explanation, evidence_ids, cognitive_ref,
                                             plan_ref, diversion_id, now)

    def _append_closure_event(self, trajectory_id: str, diversion: Mapping[str, Any],
                              outcome: Mapping[str, Any], now: str) -> dict[str, Any]:
        trajectory = self.latest(trajectory_id)
        return self._append_same_state_event(
            trajectory, "DIVERSION_CLOSED", outcome["outcome"], outcome["explanation"],
            outcome.get("supporting_evidence_ids", []), outcome.get("cognitive_state_reference"),
            outcome.get("representation_plan_reference"), now, diversion["diversion_id"],
        )

    def _same_decision_event(self, trajectory_id: str, event_type: str,
                             decision: Mapping[str, Any]) -> dict[str, Any] | None:
        for event in reversed(self.history.history_for_trajectory(trajectory_id)):
            if (event["event_type"] == event_type and event["trigger"] == decision["rule_id"]
                    and event["trajectory_version"] == self.latest(trajectory_id)["trajectory_version"]
                    and event["supporting_evidence_ids"] == sorted(set(decision["supporting_evidence_ids"]))
                    and event["decision_explanation"] == decision["explanation"]):
                return event
        return None

    def _same_outcome_event(self, trajectory_id: str, diversion_id: str,
                            outcome: Mapping[str, Any]) -> dict[str, Any] | None:
        trigger = f"{outcome['outcome']}:{outcome['rule_id']}"
        for event in reversed(self.history.history_for_trajectory(trajectory_id)):
            if (event["event_type"] == "RESUMPTION_DECIDED" and event["trigger"] == trigger
                    and event["related_diversion_id"] == diversion_id
                    and event["trajectory_version"] == self.latest(trajectory_id)["trajectory_version"]
                    and event["supporting_evidence_ids"] == sorted(set(outcome.get("supporting_evidence_ids", [])))
                    and event["decision_explanation"] == outcome["explanation"]):
                return event
        return None

    @staticmethod
    def _cognitive_ref(trajectory: Mapping[str, Any]) -> dict[str, Any] | None:
        value = trajectory["context"]["previous_cognitive_state_id"]
        return None if value is None else {"cognitive_state_id": value}

    @staticmethod
    def _plan_ref(trajectory: Mapping[str, Any]) -> dict[str, Any] | None:
        value = trajectory["context"]["previous_representation_plan_id"]
        return None if value is None else {"plan_id": value}

    @staticmethod
    def _diagnostic_ids(cognitive_state: Mapping[str, Any] | None) -> list[str]:
        return [] if cognitive_state is None else [item["recommendation_id"] for item in cognitive_state["diagnostic_recommendations"]]

    @staticmethod
    def _apply_outcome_references(trajectory: dict[str, Any], outcome: Mapping[str, Any]) -> None:
        cognitive_ref = outcome.get("cognitive_state_reference") or {}
        if cognitive_ref.get("cognitive_state_id"):
            trajectory["context"]["previous_cognitive_state_id"] = cognitive_ref["cognitive_state_id"]
        trajectory["context"]["supporting_evidence_ids"] = sorted(set(
            trajectory["context"]["supporting_evidence_ids"]
            + outcome.get("supporting_evidence_ids", [])
        ))
