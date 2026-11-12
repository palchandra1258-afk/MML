"""SQLAlchemy 2.x models and database lifecycle helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column, sessionmaker


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


CURRENT_SCHEMA_CONTRACT = "migrations/0003_f10_learning_intelligence"


class Base(DeclarativeBase):
    pass


class AppMetadata(Base):
    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)


class LearnerReference(Base):
    __tablename__ = "learner_references"

    learner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class StudentStudioProfile(Base):
    """Separate local demonstration identity, never an EdNet learner account."""

    __tablename__ = "studio_profiles"

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_type: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class StudentLearningSession(Base):
    __tablename__ = "studio_learning_sessions"
    __table_args__ = (
        Index("ix_studio_sessions_profile_activity", "profile_id", "last_activity_at"),
    )

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("studio_profiles.profile_id", ondelete="RESTRICT"), nullable=False
    )
    lesson_id: Mapped[str] = mapped_column(String(160), nullable=False)
    content_version: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)
    last_activity_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class StudentLessonProgress(Base):
    __tablename__ = "studio_lesson_progress"
    __table_args__ = (
        ForeignKeyConstraint(["profile_id"], ["studio_profiles.profile_id"], ondelete="RESTRICT"),
        Index("ix_studio_progress_profile_course", "profile_id", "course_id"),
    )

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(160), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(160), nullable=False)
    content_version: Mapped[str] = mapped_column(String(40), nullable=False)
    current_section_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    completed_section_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    started_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)
    completed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class StudentLearningAttempt(Base):
    """Append-only evaluated answer and its normalized Phase 10 evidence record."""

    __tablename__ = "studio_learning_attempts"
    __table_args__ = (
        ForeignKeyConstraint(["profile_id"], ["studio_profiles.profile_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["session_id"], ["studio_learning_sessions.session_id"], ondelete="RESTRICT"),
        UniqueConstraint("profile_id", "submission_id", name="uq_studio_attempt_submission"),
        UniqueConstraint("profile_id", "question_id", "attempt_number", name="uq_studio_attempt_question_number"),
        UniqueConstraint("profile_id", "event_sequence", name="uq_studio_attempt_event_sequence"),
        Index("ix_studio_attempts_profile_time", "profile_id", "event_timestamp"),
        Index("ix_studio_attempts_profile_lesson", "profile_id", "lesson_id"),
    )

    attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    submission_id: Mapped[str] = mapped_column(String(80), nullable=False)
    course_id: Mapped[str] = mapped_column(String(160), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(160), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(160), nullable=False)
    question_id: Mapped[str] = mapped_column(String(160), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_response: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_version: Mapped[str] = mapped_column(String(40), nullable=False)
    event_timestamp: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_record: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(40), nullable=False, default="evidence_recorded")
    behavioral_state_version: Mapped[int | None] = mapped_column(Integer, nullable=True)


class StudentBehavioralStateVersion(Base):
    """Immutable learner-scoped Phase 9 snapshot over a complete Studio prefix."""

    __tablename__ = "studio_behavioral_state_versions"
    __table_args__ = (
        ForeignKeyConstraint(["profile_id"], ["studio_profiles.profile_id"], ondelete="RESTRICT"),
        UniqueConstraint("profile_id", "source_event_sequence", name="uq_studio_state_source_sequence"),
    )

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    state_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_event_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    last_evidence_id: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_state_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state_timestamp: Mapped[str] = mapped_column(String(40), nullable=False)
    state_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class StudentLearningRecommendation(Base):
    """An immutable, evidence-linked next activity for a Studio state version."""

    __tablename__ = "studio_learning_recommendations"
    __table_args__ = (
        ForeignKeyConstraint(["profile_id"], ["studio_profiles.profile_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["profile_id", "source_state_version"],
            ["studio_behavioral_state_versions.profile_id", "studio_behavioral_state_versions.state_version"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("profile_id", "source_state_version", name="uq_studio_recommendation_state_version"),
        Index("ix_studio_recommendations_profile_created", "profile_id", "created_at"),
    )

    recommendation_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(160), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class ArtifactFile(Base):
    __tablename__ = "artifact_files"

    artifact_name: Mapped[str] = mapped_column(String(40), primary_key=True)
    source_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_mtime_ns: Mapped[int] = mapped_column(BigInteger, nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    indexed_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class ArtifactRecord(Base):
    __tablename__ = "artifact_records"
    __table_args__ = (
        ForeignKeyConstraint(["artifact_name"], ["artifact_files.artifact_name"], ondelete="CASCADE"),
        Index("ix_artifact_records_learner", "learner_id", "artifact_name"),
    )

    artifact_name: Mapped[str] = mapped_column(String(40), primary_key=True)
    record_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    record_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    line_offset: Mapped[int] = mapped_column(BigInteger, nullable=False)
    byte_length: Mapped[int] = mapped_column(Integer, nullable=False)
    record_time: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ArtifactRecordLink(Base):
    __tablename__ = "artifact_record_links"
    __table_args__ = (
        ForeignKeyConstraint(
            ["artifact_name", "record_id"],
            ["artifact_records.artifact_name", "artifact_records.record_id"],
            ondelete="CASCADE",
        ),
        Index("ix_artifact_record_links_target", "artifact_name", "linked_record_id"),
    )

    artifact_name: Mapped[str] = mapped_column(String(40), primary_key=True)
    record_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    linked_record_id: Mapped[str] = mapped_column(String(160), primary_key=True)


class TrajectoryRecord(Base):
    __tablename__ = "trajectories"

    trajectory_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    learner_id: Mapped[str] = mapped_column(
        ForeignKey("learner_references.learner_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False)
    current_status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_concept_id: Mapped[str] = mapped_column(String(160), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)


class TrajectoryVersion(Base):
    __tablename__ = "trajectory_versions"
    __table_args__ = (
        ForeignKeyConstraint(["trajectory_id"], ["trajectories.trajectory_id"], ondelete="RESTRICT"),
    )

    trajectory_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    recorded_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class TrajectoryEventRecord(Base):
    __tablename__ = "trajectory_history_events"
    __table_args__ = (
        ForeignKeyConstraint(["trajectory_id"], ["trajectories.trajectory_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["previous_event_id"], ["trajectory_history_events.event_id"], ondelete="RESTRICT"),
        UniqueConstraint("trajectory_id", "event_order", name="uq_trajectory_event_order"),
        Index("ix_trajectory_events_version", "trajectory_id", "trajectory_version"),
    )

    event_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    trajectory_id: Mapped[str] = mapped_column(String(160), nullable=False)
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
    trajectory_version: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_event_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    occurred_at: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class DiversionRecord(Base):
    __tablename__ = "diversions"

    diversion_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    learner_id: Mapped[str] = mapped_column(
        ForeignKey("learner_references.learner_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    parent_trajectory_id: Mapped[str] = mapped_column(
        ForeignKey("trajectories.trajectory_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class DiversionVersion(Base):
    __tablename__ = "diversion_versions"
    __table_args__ = (
        ForeignKeyConstraint(["diversion_id"], ["diversions.diversion_id"], ondelete="RESTRICT"),
    )

    diversion_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    recorded_at: Mapped[str] = mapped_column(String(40), nullable=False, default=utc_now)


class ContextSnapshotRecord(Base):
    __tablename__ = "trajectory_context_snapshots"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_trajectory_id", "parent_trajectory_version"],
            ["trajectory_versions.trajectory_id", "trajectory_versions.version"],
            ondelete="RESTRICT",
        ),
    )

    context_snapshot_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    parent_trajectory_id: Mapped[str] = mapped_column(String(160), nullable=False)
    parent_trajectory_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class Database:
    """Own an engine/session factory; callers control transaction boundaries."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite:") else {}
        if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
            db_path = database_url.removeprefix("sqlite:///").split("?", 1)[0]
            path = Path(db_path).expanduser()
            path.resolve().parent.mkdir(parents=True, exist_ok=True)
            try:
                file_descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            except FileExistsError:
                pass
            else:
                os.close(file_descriptor)
        self.engine: Engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
        if database_url.startswith("sqlite:"):
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False, class_=Session)

    @staticmethod
    def _enable_sqlite_foreign_keys(connection: Any, _record: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def session(self) -> Session:
        return self.session_factory()

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)
        self.ensure_schema_metadata()

    def ensure_schema_metadata(self) -> None:
        with self.session_factory.begin() as session:
            session.merge(AppMetadata(key="schema_contract", value=CURRENT_SCHEMA_CONTRACT))

    def dispose(self) -> None:
        self.engine.dispose()
