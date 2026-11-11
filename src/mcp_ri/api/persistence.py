"""SQLAlchemy 2.x models and database lifecycle helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
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
    line_offset: Mapped[int] = mapped_column(BigInteger, nullable=False)
    byte_length: Mapped[int] = mapped_column(Integer, nullable=False)
    record_time: Mapped[str | None] = mapped_column(String(64), nullable=True)


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
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
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
        with self.session_factory.begin() as session:
            session.merge(AppMetadata(key="schema_contract", value="migrations/0001_initial"))

    def dispose(self) -> None:
        self.engine.dispose()
