"""Initial schema with all models

Revision ID: 0001
Revises: 
Create Date: 2026-08-19 22:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('customer', 'agent', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email_role', 'users', ['email', 'role'], unique=False)

    # Zones table
    op.create_table(
        'zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code')
    )

    # Zone areas table
    op.create_table(
        'zone_areas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('zone_id', 'pincode', name='uq_zone_pincode')
    )
    op.create_index('ix_zone_areas_pincode_city', 'zone_areas', ['pincode', 'city'], unique=False)

    # Rate cards table
    op.create_table(
        'rate_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('order_type', sa.Enum('b2b', 'b2c', name='ordertype'), nullable=False),
        sa.Column('zone_type', sa.Enum('intra_zone', 'inter_zone', name='zonetype'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('effective_from', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('effective_to', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'order_type', 'zone_type', name='uq_rate_card_name_type')
    )
    op.create_index('ix_rate_cards_type_zone_active', 'rate_cards', ['order_type', 'zone_type', 'is_active'], unique=False)

    # Rate card rules table
    op.create_table(
        'rate_card_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rate_card_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pickup_zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('drop_zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('min_weight_kg', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('max_weight_kg', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('base_charge', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('per_kg_charge', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['rate_card_id'], ['rate_cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pickup_zone_id'], ['zones.id']),
        sa.ForeignKeyConstraint(['drop_zone_id'], ['zones.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('min_weight_kg >= 0', name='ck_min_weight_positive'),
        sa.CheckConstraint('max_weight_kg IS NULL OR max_weight_kg > min_weight_kg', name='ck_max_weight_greater'),
        sa.CheckConstraint('base_charge >= 0', name='ck_base_charge_positive'),
        sa.CheckConstraint('per_kg_charge >= 0', name='ck_per_kg_charge_positive')
    )
    op.create_index('ix_rate_rules_lookup', 'rate_card_rules', ['rate_card_id', 'pickup_zone_id', 'drop_zone_id', 'min_weight_kg'], unique=False)

    # COD surcharges table
    op.create_table(
        'cod_surcharges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rate_card_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('min_order_value', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('max_order_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('surcharge_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('min_surcharge', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('max_surcharge', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['rate_card_id'], ['rate_cards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('surcharge_percentage >= 0 AND surcharge_percentage <= 100', name='ck_surcharge_percentage'),
        sa.CheckConstraint('min_surcharge >= 0', name='ck_min_surcharge_positive'),
        sa.CheckConstraint('max_surcharge IS NULL OR max_surcharge >= min_surcharge', name='ck_max_surcharge_greater'),
        sa.CheckConstraint('max_order_value IS NULL OR max_order_value > min_order_value', name='ck_max_order_value_greater')
    )
    op.create_index('ix_cod_surcharge_lookup', 'cod_surcharges', ['rate_card_id', 'min_order_value', 'is_active'], unique=False)

    # Orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_number', sa.String(length=30), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('pickup_address', sa.Text(), nullable=False),
        sa.Column('pickup_pincode', sa.String(length=10), nullable=False),
        sa.Column('pickup_city', sa.String(length=100), nullable=True),
        sa.Column('pickup_state', sa.String(length=100), nullable=True),
        sa.Column('pickup_zone_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('drop_address', sa.Text(), nullable=False),
        sa.Column('drop_pincode', sa.String(length=10), nullable=False),
        sa.Column('drop_city', sa.String(length=100), nullable=True),
        sa.Column('drop_state', sa.String(length=100), nullable=True),
        sa.Column('drop_zone_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('length_cm', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('breadth_cm', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('height_cm', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('actual_weight_kg', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('volumetric_weight_kg', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('billable_weight_kg', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('order_type', sa.Enum('b2b', 'b2c', name='ordertype'), nullable=False),
        sa.Column('payment_type', sa.Enum('prepaid', 'cod', name='paymenttype'), nullable=False),
        sa.Column('zone_type', sa.Enum('intra_zone', 'inter_zone', name='zonetype'), nullable=False),
        sa.Column('base_charge', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('cod_surcharge', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('total_charge', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.Enum('created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'cancelled', name='orderstatus'), nullable=False, server_default='created'),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('picked_up_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['agent_id'], ['users.id']),
        sa.ForeignKeyConstraint(['pickup_zone_id'], ['zones.id']),
        sa.ForeignKeyConstraint(['drop_zone_id'], ['zones.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.CheckConstraint('actual_weight_kg > 0', name='ck_actual_weight_positive'),
        sa.CheckConstraint('billable_weight_kg >= actual_weight_kg', name='ck_billable_weight'),
        sa.CheckConstraint('total_charge >= 0', name='ck_total_charge_positive')
    )
    op.create_index('ix_orders_customer_status', 'orders', ['customer_id', 'status'], unique=False)
    op.create_index('ix_orders_agent_status', 'orders', ['agent_id', 'status'], unique=False)
    op.create_index('ix_orders_created_status', 'orders', ['created_at', 'status'], unique=False)

    # Order status history table
    op.create_table(
        'order_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_status', sa.Enum('created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'cancelled', name='orderstatus'), nullable=True),
        sa.Column('new_status', sa.Enum('created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'cancelled', name='orderstatus'), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_role', sa.Enum('customer', 'agent', 'admin', name='userrole'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('context_data', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_status_history_order_created', 'order_status_history', ['order_id', 'created_at'], unique=False)

    # Agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('available', 'busy', 'offline', name='agentstatus'), nullable=False, server_default='offline'),
        sa.Column('max_concurrent_deliveries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('current_deliveries_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('employee_id')
    )

    # Agent locations table
    op.create_table(
        'agent_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=False),
        sa.Column('accuracy_meters', sa.Integer(), nullable=True),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )

    # Delivery assignments table
    op.create_table(
        'delivery_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('is_auto_assigned', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )

    # Delivery attempts table
    op.create_table(
        'delivery_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'delivered', 'failed', name='deliveryattemptstatus'), nullable=False, server_default='pending'),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('proof_of_delivery', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', 'attempt_number', name='uq_order_attempt')
    )
    op.create_index('ix_delivery_attempts_order_agent', 'delivery_attempts', ['order_id', 'agent_id'], unique=False)

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_notifications_order_type', 'notifications', ['order_id', 'type'], unique=False)

    # Reschedule requests table
    op.create_table(
        'reschedule_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preferred_date', sa.DateTime(), nullable=False),
        sa.Column('preferred_time_slot', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('new_delivery_attempt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['new_delivery_attempt_id'], ['delivery_attempts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reschedule_order_status', 'reschedule_requests', ['order_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_reschedule_order_status', table_name='reschedule_requests')
    op.drop_table('reschedule_requests')
    op.drop_index('ix_notifications_order_type', table_name='notifications')
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_delivery_attempts_order_agent', table_name='delivery_attempts')
    op.drop_table('delivery_attempts')
    op.drop_table('delivery_assignments')
    op.drop_table('agent_locations')
    op.drop_table('agents')
    op.drop_index('ix_status_history_order_created', table_name='order_status_history')
    op.drop_table('order_status_history')
    op.drop_index('ix_orders_created_status', table_name='orders')
    op.drop_index('ix_orders_agent_status', table_name='orders')
    op.drop_index('ix_orders_customer_status', table_name='orders')
    op.drop_table('orders')
    op.drop_index('ix_cod_surcharge_lookup', table_name='cod_surcharges')
    op.drop_table('cod_surcharges')
    op.drop_index('ix_rate_rules_lookup', table_name='rate_card_rules')
    op.drop_table('rate_card_rules')
    op.drop_index('ix_rate_cards_type_zone_active', table_name='rate_cards')
    op.drop_table('rate_cards')
    op.drop_index('ix_zone_areas_pincode_city', table_name='zone_areas')
    op.drop_table('zone_areas')
    op.drop_table('zones')
    op.drop_index('ix_users_email_role', table_name='users')
    op.drop_table('users')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS ordertype')
    op.execute('DROP TYPE IF EXISTS paymenttype')
    op.execute('DROP TYPE IF EXISTS orderstatus')
    op.execute('DROP TYPE IF EXISTS agentstatus')
    op.execute('DROP TYPE IF EXISTS zonetype')
    op.execute('DROP TYPE IF EXISTS deliveryattemptstatus')
