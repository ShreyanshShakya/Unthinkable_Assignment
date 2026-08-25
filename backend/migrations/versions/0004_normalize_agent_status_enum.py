"""Normalize agentstatus PostgreSQL enum labels to match SQLAlchemy Enum.

Revision ID: 0004
Revises: 0003
"""

from alembic import op


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLAlchemy Enum(AgentStatus) persists enum member names by default
    # (AVAILABLE/BUSY/OFFLINE). Existing production data was created with
    # lowercase labels, so normalize the PostgreSQL enum to the labels the
    # ORM expects when reading rows back.
    op.execute("ALTER TYPE agentstatus RENAME VALUE 'available' TO 'AVAILABLE'")
    op.execute("ALTER TYPE agentstatus RENAME VALUE 'busy' TO 'BUSY'")
    op.execute("ALTER TYPE agentstatus RENAME VALUE 'offline' TO 'OFFLINE'")


def downgrade() -> None:
    op.execute("ALTER TYPE agentstatus RENAME VALUE 'AVAILABLE' TO 'available'")
    op.execute("ALTER TYPE agentstatus RENAME VALUE 'BUSY' TO 'busy'")
    op.execute("ALTER TYPE agentstatus RENAME VALUE 'OFFLINE' TO 'offline'")
