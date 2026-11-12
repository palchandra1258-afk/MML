"""Application services joining artifact lookup and Phase 13 domain logic."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mcp_ri.trajectory.history import TrajectoryHistory
from mcp_ri.trajectory.trajectory_builder import build_trajectory
from mcp_ri.trajectory.trajectory_manager import TrajectoryManager

from .artifact_index import indexed_status, read_indexed_record
from .errors import APIError
from .persistence import (
    ArtifactRecord,
    ArtifactRecordLink,
    DiversionRecord,
    LearnerReference,
    TrajectoryEventRecord,
    TrajectoryRecord,
    TrajectoryVersion,
    utc_now,
)
from .settings import APISettings


class ArtifactService:
    def __init__(self, settings: APISettings) -> None:
        self.settings = settings

    def status(self, session: Session) -> dict[str, dict[str, Any]]:
        return indexed_status(session, self.settings.artifact_paths())

    def ready_names(self, session: Session) -> set[str]:
        return {name for name, info in self.status(session).items() if info["available"]}

    def learners(self, session: Session, *, limit: int, offset: int) -> tuple[list[str], int]:
        ready = self.ready_names(session)
        ids = set(session.scalars(select(LearnerReference.learner_id)).all())
        if ready:
            ids.update(session.scalars(
                select(ArtifactRecord.learner_id)
                .where(ArtifactRecord.artifact_name.in_(ready))
                .distinct()
            ).all())
        ordered = sorted(ids)
        return ordered[offset:offset + limit], len(ordered)

    def available_for_learner(self, session: Session, learner_id: str) -> list[str]:
        ready = self.ready_names(session)
        names: set[str] = set()
        if ready:
            names.update(session.scalars(
                select(ArtifactRecord.artifact_name)
                .where(ArtifactRecord.learner_id == learner_id, ArtifactRecord.artifact_name.in_(ready))
                .distinct()
            ).all())
        if session.get(LearnerReference, learner_id):
            names.add("application")
        return sorted(names)

    def _ready(self, session: Session, artifact_name: str) -> Path:
        path = self.settings.artifact_paths()[artifact_name]
        if not self.status(session)[artifact_name]["available"]:
            raise APIError(503, "ARTIFACT_INDEX_UNAVAILABLE", "The requested research artifact is not indexed or has changed.")
        return path

    def get_record(self, session: Session, artifact_name: str, record_id: str) -> dict[str, Any] | None:
        path = self._ready(session, artifact_name)
        row = session.get(ArtifactRecord, (artifact_name, record_id))
        if row is None:
            return None
        return read_indexed_record(path, row.line_offset, row.byte_length)

    def record_for_learner(
        self,
        session: Session,
        artifact_name: str,
        record_id: str,
        learner_id: str,
    ) -> dict[str, Any] | None:
        record = self.get_record(session, artifact_name, record_id)
        if record is None or record.get("learner_id") != learner_id:
            return None
        return record

    def list_records(
        self,
        session: Session,
        artifact_name: str,
        learner_id: str,
        *,
        limit: int,
        offset: int,
        record_type: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        path = self._ready(session, artifact_name)
        query = select(ArtifactRecord).where(
            ArtifactRecord.artifact_name == artifact_name,
            ArtifactRecord.learner_id == learner_id,
        )
        if record_type is not None:
            query = query.where(ArtifactRecord.record_type == record_type)
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = session.scalars(
            query.order_by(ArtifactRecord.record_time, ArtifactRecord.line_offset)
            .limit(limit).offset(offset)
        ).all()
        return [read_indexed_record(path, row.line_offset, row.byte_length) for row in rows], total

    def latest_record(self, session: Session, artifact_name: str, learner_id: str) -> dict[str, Any] | None:
        path = self._ready(session, artifact_name)
        row = session.scalar(
            select(ArtifactRecord)
            .where(ArtifactRecord.artifact_name == artifact_name, ArtifactRecord.learner_id == learner_id)
            .order_by(ArtifactRecord.record_time.desc(), ArtifactRecord.line_offset.desc())
            .limit(1)
        )
        return None if row is None else read_indexed_record(path, row.line_offset, row.byte_length)

    def groups_for_evidence(
        self,
        session: Session,
        learner_id: str,
        evidence_ids: list[str],
    ) -> tuple[bool, dict[str, list[dict[str, Any]]]]:
        if not self.status(session)["phase10_groups"]["available"]:
            return False, {}
        if not evidence_ids:
            return True, {}
        path = self.settings.artifact_paths()["phase10_groups"]
        rows = session.execute(
            select(ArtifactRecord, ArtifactRecordLink.linked_record_id)
            .join(ArtifactRecordLink, (
                (ArtifactRecordLink.artifact_name == ArtifactRecord.artifact_name)
                & (ArtifactRecordLink.record_id == ArtifactRecord.record_id)
            ))
            .where(
                ArtifactRecord.artifact_name == "phase10_groups",
                ArtifactRecord.learner_id == learner_id,
                ArtifactRecordLink.linked_record_id.in_(evidence_ids),
            )
            .order_by(ArtifactRecord.record_id)
        ).all()
        groups_by_id: dict[str, dict[str, Any]] = {}
        result: dict[str, list[dict[str, Any]]] = {evidence_id: [] for evidence_id in evidence_ids}
        for row, evidence_id in rows:
            group = groups_by_id.get(row.record_id)
            if group is None:
                group = read_indexed_record(path, row.line_offset, row.byte_length)
                groups_by_id[row.record_id] = group
            result[evidence_id].append(group)
        return True, result


class ResearchService:
    """Read-only Phase 9–12 snapshots plus learner availability metadata."""

    def __init__(self, artifacts: ArtifactService) -> None:
        self.artifacts = artifacts

    def list_learners(self, session: Session, *, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        learners, total = self.artifacts.learners(session, limit=limit, offset=offset)
        return [
            {"learner_id": learner_id,
             "available_data": self.artifacts.available_for_learner(session, learner_id)}
            for learner_id in learners
        ], total

    def learner_detail(self, session: Session, learner_id: str) -> dict[str, Any]:
        available = self.artifacts.available_for_learner(session, learner_id)
        if not available:
            raise APIError(404, "RESOURCE_NOT_FOUND", "The requested learner was not found.")
        count = session.scalar(
            select(func.count()).select_from(TrajectoryRecord).where(TrajectoryRecord.learner_id == learner_id)
        ) or 0
        source = "application" if available == ["application"] else "research_artifacts"
        return {
            "learner_id": learner_id,
            "available_data": available,
            "trajectory_count": count,
            "source": source,
        }

    def behavioral_state(self, session: Session, learner_id: str) -> dict[str, Any]:
        record = self.artifacts.get_record(session, "phase9_states", learner_id)
        if record is None:
            raise APIError(404, "RESOURCE_NOT_FOUND", "No behavioral state is available for this learner.")
        return record

    def cognitive_state(self, session: Session, learner_id: str) -> dict[str, Any]:
        record = self.artifacts.latest_record(session, "phase11_states", learner_id)
        if record is None:
            raise APIError(404, "RESOURCE_NOT_FOUND", "No cognitive-state estimate is available for this learner.")
        return record

    def evidence(
        self, session: Session, learner_id: str, *, limit: int, offset: int, evidence_type: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        records, total = self.artifacts.list_records(
            session, "phase10_evidence", learner_id,
            limit=limit, offset=offset, record_type=evidence_type,
        )
        return self._annotate_evidence(session, learner_id, records), total

    def evidence_record(self, session: Session, learner_id: str, evidence_id: str) -> dict[str, Any]:
        record = self.artifacts.record_for_learner(session, "phase10_evidence", evidence_id, learner_id)
        if record is None:
            raise APIError(404, "EVIDENCE_NOT_FOUND", "The requested evidence record was not found.")
        return self._annotate_evidence(session, learner_id, [record])[0]

    def _annotate_evidence(
        self,
        session: Session,
        learner_id: str,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        available, groups = self.artifacts.groups_for_evidence(
            session, learner_id, [record["evidence_id"] for record in records],
        )
        for record in records:
            related_groups = groups.get(record["evidence_id"], [])
            record["grouping_information"] = related_groups
            links: dict[tuple[str, str], dict[str, Any]] = {}
            for group in related_groups:
                for link in group.get("alignment_links", []):
                    if record["evidence_id"] in {link["left_evidence_id"], link["right_evidence_id"]}:
                        links[(link["left_evidence_id"], link["right_evidence_id"])] = link
            record["alignment_links"] = list(links.values())
            record["grouping_annotations_available"] = available
        return records

    def representations(self, session: Session, learner_id: str, *, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        return self.artifacts.list_records(
            session, "phase12_plans", learner_id, limit=limit, offset=offset,
        )

    def representation(self, session: Session, learner_id: str, plan_id: str) -> dict[str, Any]:
        record = self.artifacts.record_for_learner(session, "phase12_plans", plan_id, learner_id)
        if record is None:
            raise APIError(404, "RESOURCE_NOT_FOUND", "The requested representation plan was not found.")
        return record


class TrajectoryService:
    """Use Phase 13 builders/managers while committing durable versions/events."""

    def __init__(self, artifacts: ArtifactService) -> None:
        self.artifacts = artifacts

    @staticmethod
    def _page_query(session: Session, model: Any, learner_id: str, *, limit: int, offset: int) -> tuple[list[Any], int]:
        query = select(model).where(model.learner_id == learner_id)
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = session.scalars(query.order_by(model.trajectory_id if model is TrajectoryRecord else model.diversion_id)
                               .limit(limit).offset(offset)).all()
        return rows, total

    def list_trajectories(self, session: Session, learner_id: str, *, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        rows, total = self._page_query(session, TrajectoryRecord, learner_id, limit=limit, offset=offset)
        return [row.snapshot for row in rows], total

    def trajectory(self, session: Session, learner_id: str, trajectory_id: str) -> dict[str, Any]:
        row = session.get(TrajectoryRecord, trajectory_id)
        if row is None or row.learner_id != learner_id:
            raise APIError(404, "RESOURCE_NOT_FOUND", "The requested trajectory was not found.")
        return row.snapshot

    def trajectory_history(
        self, session: Session, learner_id: str, trajectory_id: str, *, limit: int, offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self.trajectory(session, learner_id, trajectory_id)
        query = select(TrajectoryEventRecord).where(TrajectoryEventRecord.trajectory_id == trajectory_id)
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        events = session.scalars(query.order_by(TrajectoryEventRecord.event_order).limit(limit).offset(offset)).all()
        return [row.payload for row in events], total

    def list_diversions(self, session: Session, learner_id: str, *, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        rows, total = self._page_query(session, DiversionRecord, learner_id, limit=limit, offset=offset)
        return [row.snapshot for row in rows], total

    def diversion(self, session: Session, learner_id: str, diversion_id: str) -> dict[str, Any]:
        row = session.get(DiversionRecord, diversion_id)
        if row is None or row.learner_id != learner_id:
            raise APIError(404, "RESOURCE_NOT_FOUND", "The requested diversion was not found.")
        return row.snapshot

    def _check_reference(self, session: Session, artifact_name: str, record_id: str, learner_id: str) -> None:
        record = self.artifacts.record_for_learner(session, artifact_name, record_id, learner_id)
        if record is None:
            raise APIError(422, "INVALID_REFERENCE", "A supplied state or evidence reference is unavailable for this learner.")

    def create_trajectory(self, session: Session, learner_id: str, request: Any) -> dict[str, Any]:
        with session.begin():
            if not self.artifacts.available_for_learner(session, learner_id):
                raise APIError(404, "RESOURCE_NOT_FOUND", "The requested learner was not found.")
            if request.previous_cognitive_state_id:
                self._check_reference(session, "phase11_states", request.previous_cognitive_state_id, learner_id)
            if request.previous_representation_plan_id:
                self._check_reference(session, "phase12_plans", request.previous_representation_plan_id, learner_id)
            for evidence_id in request.supporting_evidence_ids:
                self._check_reference(session, "phase10_evidence", evidence_id, learner_id)
            learner = session.get(LearnerReference, learner_id)
            if learner is None:
                learner = LearnerReference(learner_id=learner_id, source="research_artifacts")
                session.add(learner)
                session.flush()
            now = datetime.now(timezone.utc).isoformat()
            try:
                trajectory = build_trajectory(
                    learner_id,
                    request.target_concept_id,
                    request.primary_learning_goal,
                    target_skill_ids=request.target_skill_ids,
                    learning_objectives=request.learning_objectives,
                    previous_representation_plan_id=request.previous_representation_plan_id,
                    previous_cognitive_state_id=request.previous_cognitive_state_id,
                    supporting_evidence_ids=request.supporting_evidence_ids,
                    created_at=now,
                )
                manager = TrajectoryManager()
                created = manager.create(trajectory)
            except (ValueError, KeyError) as exc:
                raise APIError(422, "INVALID_TRAJECTORY", "The trajectory request does not satisfy Phase 13 rules.") from exc
            session.add(TrajectoryRecord(
                trajectory_id=created["trajectory_id"],
                learner_id=learner_id,
                current_version=created["trajectory_version"],
                current_status=created["current_status"],
                current_concept_id=created["current_concept_id"],
                snapshot=created,
                created_at=created["created_at"],
                updated_at=created["updated_at"],
            ))
            session.flush()
            session.add(TrajectoryVersion(
                trajectory_id=created["trajectory_id"], version=created["trajectory_version"],
                snapshot=created, recorded_at=utc_now(),
            ))
            for order, event in enumerate(manager.history.history_for_trajectory(created["trajectory_id"]), start=1):
                session.add(TrajectoryEventRecord(
                    event_id=event["event_id"], trajectory_id=created["trajectory_id"],
                    event_order=order, trajectory_version=event["trajectory_version"],
                    previous_event_id=event["previous_event_id"], occurred_at=event["occurred_at"], payload=event,
                ))
            session.flush()
            return created

    def _manager_from_db(self, session: Session, trajectory_id: str) -> tuple[TrajectoryManager, int]:
        events = session.scalars(
            select(TrajectoryEventRecord).where(TrajectoryEventRecord.trajectory_id == trajectory_id)
            .order_by(TrajectoryEventRecord.event_order)
        ).all()
        history = TrajectoryHistory()
        try:
            for row in events:
                history.append_event(row.payload)
            manager = TrajectoryManager(history=history)
            manager.restore(trajectory_id)
        except (ValueError, KeyError) as exc:
            raise APIError(500, "HISTORY_INTEGRITY_ERROR", "The stored trajectory history could not be reconstructed.") from exc
        return manager, len(events)

    def apply_action(
        self,
        session: Session,
        learner_id: str,
        trajectory_id: str,
        request: Any,
    ) -> dict[str, Any]:
        try:
            with session.begin():
                row = session.get(TrajectoryRecord, trajectory_id)
                if row is None or row.learner_id != learner_id:
                    raise APIError(404, "RESOURCE_NOT_FOUND", "The requested trajectory was not found.")
                if request.action == "activate" and request.evidence_ids:
                    raise APIError(422, "INVALID_REQUEST", "The Phase 13 activate operation does not accept evidence IDs.")
                for evidence_id in request.evidence_ids:
                    self._check_reference(session, "phase10_evidence", evidence_id, learner_id)
                expected_version = row.current_version
                manager, prior_event_count = self._manager_from_db(session, trajectory_id)
                try:
                    if request.action == "activate":
                        result = manager.activate(trajectory_id)
                    elif request.action == "pause":
                        if not request.reason or not request.reason.strip():
                            raise APIError(422, "INVALID_REQUEST", "A non-empty reason is required to pause a trajectory.")
                        result = manager.pause(trajectory_id, reason=request.reason, evidence_ids=request.evidence_ids)
                    else:
                        result = manager.advance_step(trajectory_id, evidence_ids=request.evidence_ids)
                except APIError:
                    raise
                except (ValueError, KeyError, StopIteration) as exc:
                    raise APIError(409, "INVALID_STATE_TRANSITION", "The requested action is invalid for the current trajectory state.") from exc
                latest = manager.latest(trajectory_id)
                if latest["trajectory_version"] != expected_version:
                    changed = session.execute(
                        update(TrajectoryRecord)
                        .where(TrajectoryRecord.trajectory_id == trajectory_id,
                               TrajectoryRecord.current_version == expected_version)
                        .values(
                            current_version=latest["trajectory_version"],
                            current_status=latest["current_status"],
                            current_concept_id=latest["current_concept_id"],
                            snapshot=latest,
                            updated_at=latest["updated_at"],
                        )
                    ).rowcount
                    if changed != 1:
                        raise APIError(409, "CONCURRENT_UPDATE", "The trajectory changed during this request; reload it and retry.")
                    session.add(TrajectoryVersion(
                        trajectory_id=trajectory_id,
                        version=latest["trajectory_version"],
                        snapshot=latest,
                        recorded_at=utc_now(),
                    ))
                new_events = manager.history.history_for_trajectory(trajectory_id)[prior_event_count:]
                for order, event in enumerate(new_events, start=prior_event_count + 1):
                    session.add(TrajectoryEventRecord(
                        event_id=event["event_id"], trajectory_id=trajectory_id,
                        event_order=order, trajectory_version=event["trajectory_version"],
                        previous_event_id=event["previous_event_id"], occurred_at=event["occurred_at"], payload=event,
                    ))
                session.flush()
                return latest
        except IntegrityError as exc:
            raise APIError(409, "RESOURCE_CONFLICT", "The trajectory update conflicted with a stored version.") from exc
