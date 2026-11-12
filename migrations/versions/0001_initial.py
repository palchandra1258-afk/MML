"""Initial backend application and immutable history schema."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_metadata",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.String(500), nullable=False),
    )
    op.create_table(
        "learner_references",
        sa.Column("learner_id", sa.String(128), primary_key=True),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_table(
        "artifact_files",
        sa.Column("artifact_name", sa.String(40), primary_key=True),
        sa.Column("source_size", sa.BigInteger(), nullable=False),
        sa.Column("source_mtime_ns", sa.BigInteger(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("indexed_at", sa.String(40), nullable=False),
    )
    op.create_table(
        "artifact_records",
        sa.Column("artifact_name", sa.String(40), nullable=False),
        sa.Column("record_id", sa.String(160), nullable=False),
        sa.Column("learner_id", sa.String(128), nullable=False),
        sa.Column("record_type", sa.String(80), nullable=True),
        sa.Column("line_offset", sa.BigInteger(), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("record_time", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(["artifact_name"], ["artifact_files.artifact_name"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("artifact_name", "record_id"),
    )
    op.create_index("ix_artifact_records_learner", "artifact_records", ["learner_id", "artifact_name"])
    op.create_table(
        "artifact_record_links",
        sa.Column("artifact_name", sa.String(40), nullable=False),
        sa.Column("record_id", sa.String(160), nullable=False),
        sa.Column("linked_record_id", sa.String(160), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_name", "record_id"],
            ["artifact_records.artifact_name", "artifact_records.record_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("artifact_name", "record_id", "linked_record_id"),
    )
    op.create_index("ix_artifact_record_links_target", "artifact_record_links", ["artifact_name", "linked_record_id"])
    op.create_table(
        "trajectories",
        sa.Column("trajectory_id", sa.String(160), primary_key=True),
        sa.Column("learner_id", sa.String(128), sa.ForeignKey("learner_references.learner_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("current_status", sa.String(32), nullable=False),
        sa.Column("current_concept_id", sa.String(160), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_trajectories_learner_id", "trajectories", ["learner_id"])
    op.create_table(
        "trajectory_versions",
        sa.Column("trajectory_id", sa.String(160), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["trajectory_id"], ["trajectories.trajectory_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("trajectory_id", "version"),
    )
    op.create_table(
        "trajectory_history_events",
        sa.Column("event_id", sa.String(160), primary_key=True),
        sa.Column("trajectory_id", sa.String(160), nullable=False),
        sa.Column("event_order", sa.Integer(), nullable=False),
        sa.Column("trajectory_version", sa.Integer(), nullable=False),
        sa.Column("previous_event_id", sa.String(160), nullable=True),
        sa.Column("occurred_at", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["trajectory_id"], ["trajectories.trajectory_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["previous_event_id"], ["trajectory_history_events.event_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("trajectory_id", "event_order", name="uq_trajectory_event_order"),
    )
    op.create_index("ix_trajectory_events_version", "trajectory_history_events", ["trajectory_id", "trajectory_version"])
    op.create_table(
        "diversions",
        sa.Column("diversion_id", sa.String(160), primary_key=True),
        sa.Column("learner_id", sa.String(128), sa.ForeignKey("learner_references.learner_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("parent_trajectory_id", sa.String(160), sa.ForeignKey("trajectories.trajectory_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
    )
    op.create_index("ix_diversions_learner_id", "diversions", ["learner_id"])
    op.create_index("ix_diversions_parent_trajectory_id", "diversions", ["parent_trajectory_id"])
    op.create_table(
        "diversion_versions",
        sa.Column("diversion_id", sa.String(160), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["diversion_id"], ["diversions.diversion_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("diversion_id", "version"),
    )
    op.create_table(
        "trajectory_context_snapshots",
        sa.Column("context_snapshot_id", sa.String(160), primary_key=True),
        sa.Column("parent_trajectory_id", sa.String(160), nullable=False),
        sa.Column("parent_trajectory_version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_trajectory_id", "parent_trajectory_version"],
            ["trajectory_versions.trajectory_id", "trajectory_versions.version"],
            ondelete="RESTRICT",
        ),
    )
    op.get_bind().execute(sa.text(
        "INSERT INTO app_metadata (key, value) VALUES ('schema_contract', 'migrations/0001_initial')"
    ))


def downgrade() -> None:
    op.drop_table("trajectory_context_snapshots")
    op.drop_table("diversion_versions")
    op.drop_index("ix_diversions_parent_trajectory_id", table_name="diversions")
    op.drop_index("ix_diversions_learner_id", table_name="diversions")
    op.drop_table("diversions")
    op.drop_index("ix_trajectory_events_version", table_name="trajectory_history_events")
    op.drop_table("trajectory_history_events")
    op.drop_table("trajectory_versions")
    op.drop_index("ix_trajectories_learner_id", table_name="trajectories")
    op.drop_table("trajectories")
    op.drop_index("ix_artifact_record_links_target", table_name="artifact_record_links")
    op.drop_table("artifact_record_links")
    op.drop_index("ix_artifact_records_learner", table_name="artifact_records")
    op.drop_table("artifact_records")
    op.drop_table("artifact_files")
    op.drop_table("learner_references")
    op.drop_table("app_metadata")
