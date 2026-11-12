"""Add isolated Student Studio curriculum activity persistence."""

from alembic import op
import sqlalchemy as sa


revision = "0002_learning_studio"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "studio_profiles",
        sa.Column("profile_id", sa.String(128), primary_key=True),
        sa.Column("profile_type", sa.String(40), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_table(
        "studio_learning_sessions",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(128), sa.ForeignKey("studio_profiles.profile_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lesson_id", sa.String(160), nullable=False),
        sa.Column("content_version", sa.String(40), nullable=False),
        sa.Column("started_at", sa.String(40), nullable=False),
        sa.Column("last_activity_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_studio_sessions_profile_activity", "studio_learning_sessions", ["profile_id", "last_activity_at"])
    op.create_table(
        "studio_lesson_progress",
        sa.Column("profile_id", sa.String(128), sa.ForeignKey("studio_profiles.profile_id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("lesson_id", sa.String(160), primary_key=True),
        sa.Column("course_id", sa.String(160), nullable=False),
        sa.Column("topic_id", sa.String(160), nullable=False),
        sa.Column("content_version", sa.String(40), nullable=False),
        sa.Column("current_section_id", sa.String(160), nullable=True),
        sa.Column("completed_section_ids", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
        sa.Column("completed_at", sa.String(40), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
    )
    op.create_index("ix_studio_progress_profile_course", "studio_lesson_progress", ["profile_id", "course_id"])
    op.create_table(
        "studio_learning_attempts",
        sa.Column("attempt_id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(128), sa.ForeignKey("studio_profiles.profile_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("studio_learning_sessions.session_id", ondelete="RESTRICT"), nullable=True),
        sa.Column("submission_id", sa.String(80), nullable=False),
        sa.Column("course_id", sa.String(160), nullable=False),
        sa.Column("topic_id", sa.String(160), nullable=False),
        sa.Column("lesson_id", sa.String(160), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("submitted_response", sa.JSON(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("feedback", sa.JSON(), nullable=False),
        sa.Column("content_version", sa.String(40), nullable=False),
        sa.Column("event_timestamp", sa.String(40), nullable=False),
        sa.Column("evidence_record", sa.JSON(), nullable=False),
        sa.UniqueConstraint("profile_id", "submission_id", name="uq_studio_attempt_submission"),
        sa.UniqueConstraint("profile_id", "question_id", "attempt_number", name="uq_studio_attempt_question_number"),
        sa.UniqueConstraint("profile_id", "event_sequence", name="uq_studio_attempt_event_sequence"),
    )
    op.create_index("ix_studio_attempts_profile_time", "studio_learning_attempts", ["profile_id", "event_timestamp"])
    op.create_index("ix_studio_attempts_profile_lesson", "studio_learning_attempts", ["profile_id", "lesson_id"])
    op.execute(sa.text(
        "UPDATE app_metadata SET value='migrations/0002_learning_studio' WHERE key='schema_contract'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE app_metadata SET value='migrations/0001_initial' WHERE key='schema_contract'"
    ))
    op.drop_index("ix_studio_attempts_profile_lesson", table_name="studio_learning_attempts")
    op.drop_index("ix_studio_attempts_profile_time", table_name="studio_learning_attempts")
    op.drop_table("studio_learning_attempts")
    op.drop_index("ix_studio_progress_profile_course", table_name="studio_lesson_progress")
    op.drop_table("studio_lesson_progress")
    op.drop_index("ix_studio_sessions_profile_activity", table_name="studio_learning_sessions")
    op.drop_table("studio_learning_sessions")
    op.drop_table("studio_profiles")
