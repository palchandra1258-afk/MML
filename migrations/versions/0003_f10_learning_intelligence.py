"""Persist Student Studio behavioral-state versions and recommendations."""

from alembic import op
import sqlalchemy as sa


revision = "0003_f10_learning_intelligence"
down_revision = "0002_learning_studio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "studio_learning_attempts",
        sa.Column("processing_status", sa.String(40), nullable=False, server_default="evidence_recorded"),
    )
    op.add_column(
        "studio_learning_attempts",
        sa.Column("behavioral_state_version", sa.Integer(), nullable=True),
    )
    op.create_table(
        "studio_behavioral_state_versions",
        sa.Column("profile_id", sa.String(128), sa.ForeignKey("studio_profiles.profile_id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("state_version", sa.Integer(), primary_key=True),
        sa.Column("source_event_sequence", sa.Integer(), nullable=False),
        sa.Column("last_evidence_id", sa.String(80), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("previous_state_version", sa.Integer(), nullable=True),
        sa.Column("state_timestamp", sa.String(40), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.UniqueConstraint("profile_id", "source_event_sequence", name="uq_studio_state_source_sequence"),
    )
    op.create_table(
        "studio_learning_recommendations",
        sa.Column("recommendation_id", sa.String(80), primary_key=True),
        sa.Column("profile_id", sa.String(128), nullable=False),
        sa.Column("source_state_version", sa.Integer(), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False),
        sa.Column("topic_id", sa.String(160), nullable=False),
        sa.Column("lesson_id", sa.String(160), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["studio_profiles.profile_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["profile_id", "source_state_version"],
            ["studio_behavioral_state_versions.profile_id", "studio_behavioral_state_versions.state_version"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("profile_id", "source_state_version", name="uq_studio_recommendation_state_version"),
    )
    op.create_index(
        "ix_studio_recommendations_profile_created",
        "studio_learning_recommendations",
        ["profile_id", "created_at"],
    )
    op.execute(sa.text(
        "UPDATE app_metadata SET value='migrations/0003_f10_learning_intelligence' WHERE key='schema_contract'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE app_metadata SET value='migrations/0002_learning_studio' WHERE key='schema_contract'"
    ))
    op.drop_index("ix_studio_recommendations_profile_created", table_name="studio_learning_recommendations")
    op.drop_table("studio_learning_recommendations")
    op.drop_table("studio_behavioral_state_versions")
    op.drop_column("studio_learning_attempts", "behavioral_state_version")
    op.drop_column("studio_learning_attempts", "processing_status")
