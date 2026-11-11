"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${("\n    ").join(upgrade_ops) if upgrade_ops else "pass"}


def downgrade() -> None:
    ${("\n    ").join(downgrade_ops) if downgrade_ops else "pass"}
