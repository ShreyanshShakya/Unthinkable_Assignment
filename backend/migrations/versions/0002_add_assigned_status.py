"""Add ASSIGNED order status

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ASSIGNED to the orderstatus enum
    op.execute("ALTER TYPE orderstatus ADD VALUE 'assigned'")


def downgrade() -> None:
    # Remove ASSIGNED from the orderstatus enum
    # Note: This requires that no orders have this status
    op.execute("DELETE FROM orders WHERE status = 'assigned'")
    op.execute("DELETE FROM order_status_history WHERE new_status = 'assigned' OR old_status = 'assigned'")
    # Can't easily remove enum value in PostgreSQL without recreating the type
    # This is a limitation - in production you'd need to recreate the enum