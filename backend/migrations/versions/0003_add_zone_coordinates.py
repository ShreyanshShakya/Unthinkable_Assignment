"""Add latitude/longitude to Zone

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('zones', sa.Column('latitude', sa.Numeric(9, 6), nullable=True))
    op.add_column('zones', sa.Column('longitude', sa.Numeric(9, 6), nullable=True))


def downgrade() -> None:
    op.drop_column('zones', 'latitude')
    op.drop_column('zones', 'longitude')