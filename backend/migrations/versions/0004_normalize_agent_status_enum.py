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
    # (AVAILABLE/BUSY/OFFLINE). Existing production data may still contain
    # lowercase labels, so normalize them. The checks make this migration
    # safe if the enum was already fixed manually in production.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'agentstatus' AND e.enumlabel = 'available'
            ) THEN
                ALTER TYPE agentstatus RENAME VALUE 'available' TO 'AVAILABLE';
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'agentstatus' AND e.enumlabel = 'busy'
            ) THEN
                ALTER TYPE agentstatus RENAME VALUE 'busy' TO 'BUSY';
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'agentstatus' AND e.enumlabel = 'offline'
            ) THEN
                ALTER TYPE agentstatus RENAME VALUE 'offline' TO 'OFFLINE';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'agentstatus' AND e.enumlabel = 'AVAILABLE'
            ) THEN
                ALTER TYPE agentstatus RENAME VALUE 'AVAILABLE' TO 'available';
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'agentstatus' AND e.enumlabel = 'BUSY'
            ) THEN
                ALTER TYPE agentstatus RENAME VALUE 'BUSY' TO 'busy';
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'agentstatus' AND e.enumlabel = 'OFFLINE'
            ) THEN
                ALTER TYPE agentstatus RENAME VALUE 'OFFLINE' TO 'offline';
            END IF;
        END $$;
    """)
