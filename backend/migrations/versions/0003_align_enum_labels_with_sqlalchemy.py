"""Align PostgreSQL enum labels with SQLAlchemy's PEP-435 enum mapping.

Revision ID: 0003
Revises: 0002

The ORM models use Python enums such as OrderStatus.ASSIGNED. SQLAlchemy
persists enum member names by default (e.g. ``ASSIGNED``), while the initial
schema stored the enum values (e.g. ``assigned``). This migration makes the
PostgreSQL enum labels match the ORM mapping without changing the Python/API
enum values.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_enum_values(enum_name: str, values: Sequence[str]) -> None:
    for value in values:
        op.execute(
            f"ALTER TYPE {enum_name} RENAME VALUE '{value}' TO '{value.upper()}'"
        )


def upgrade() -> None:
    _rename_enum_values("userrole", ["customer", "agent", "admin"])
    _rename_enum_values("ordertype", ["b2b", "b2c"])
    _rename_enum_values("paymenttype", ["prepaid", "cod"])
    _rename_enum_values(
        "orderstatus",
        [
            "created",
            "assigned",
            "picked_up",
            "in_transit",
            "out_for_delivery",
            "delivered",
            "failed",
            "cancelled",
        ],
    )
    _rename_enum_values("agentstatus", ["available", "busy", "offline"])
    _rename_enum_values("zonetype", ["intra_zone", "inter_zone"])
    _rename_enum_values(
        "deliveryattemptstatus", ["pending", "in_progress", "delivered", "failed"]
    )


def downgrade() -> None:
    # Reverse the label changes. This keeps the migration reversible for
    # environments where the previous lowercase enum convention is required.
    _rename_enum_values("deliveryattemptstatus", ["PENDING", "IN_PROGRESS", "DELIVERED", "FAILED"])
    _rename_enum_values("zonetype", ["INTRA_ZONE", "INTER_ZONE"])
    _rename_enum_values("agentstatus", ["AVAILABLE", "BUSY", "OFFLINE"])
    _rename_enum_values(
        "orderstatus",
        [
            "CREATED",
            "ASSIGNED",
            "PICKED_UP",
            "IN_TRANSIT",
            "OUT_FOR_DELIVERY",
            "DELIVERED",
            "FAILED",
            "CANCELLED",
        ],
    )
    _rename_enum_values("paymenttype", ["PREPAID", "COD"])
    _rename_enum_values("ordertype", ["B2B", "B2C"])
    _rename_enum_values("userrole", ["CUSTOMER", "AGENT", "ADMIN"])
