import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Enum, ForeignKey, 
    Numeric, Text, Index, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"


class OrderType(str, enum.Enum):
    B2B = "b2b"
    B2C = "b2c"


class PaymentType(str, enum.Enum):
    PREPAID = "prepaid"
    COD = "cod"


class OrderStatus(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ZoneType(str, enum.Enum):
    INTRA_ZONE = "intra_zone"
    INTER_ZONE = "inter_zone"


class DeliveryAttemptStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
    assigned_orders = relationship("Order", back_populates="agent", foreign_keys="Order.agent_id")
    agent_profile = relationship("Agent", back_populates="user", uselist=False)
    status_history = relationship("OrderStatusHistory", back_populates="actor")
    notifications = relationship("Notification", back_populates="user")
    
    __table_args__ = (
        Index("ix_users_email_role", "email", "role"),
    )


class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    areas = relationship("ZoneArea", back_populates="zone", cascade="all, delete-orphan")
    pickup_rates = relationship("RateCardRule", back_populates="pickup_zone", foreign_keys="RateCardRule.pickup_zone_id")
    drop_rates = relationship("RateCardRule", back_populates="drop_zone", foreign_keys="RateCardRule.drop_zone_id")
    agents = relationship("Agent", back_populates="zone")


class ZoneArea(Base):
    __tablename__ = "zone_areas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False, index=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    zone = relationship("Zone", back_populates="areas")
    
    __table_args__ = (
        UniqueConstraint("zone_id", "pincode", name="uq_zone_pincode"),
        Index("ix_zone_areas_pincode_city", "pincode", "city"),
    )


class RateCard(Base):
    __tablename__ = "rate_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False, index=True)
    zone_type = Column(Enum(ZoneType), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    rules = relationship("RateCardRule", back_populates="rate_card", cascade="all, delete-orphan")
    cod_surcharges = relationship("CODSurcharge", back_populates="rate_card", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("name", "order_type", "zone_type", name="uq_rate_card_name_type"),
        Index("ix_rate_cards_type_zone_active", "order_type", "zone_type", "is_active"),
    )


class RateCardRule(Base):
    __tablename__ = "rate_card_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_card_id = Column(UUID(as_uuid=True), ForeignKey("rate_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    pickup_zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=False, index=True)
    drop_zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=False, index=True)
    min_weight_kg = Column(Numeric(10, 3), nullable=False)
    max_weight_kg = Column(Numeric(10, 3), nullable=True)  # NULL means no upper limit
    base_charge = Column(Numeric(10, 2), nullable=False)
    per_kg_charge = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    rate_card = relationship("RateCard", back_populates="rules")
    pickup_zone = relationship("Zone", back_populates="pickup_rates", foreign_keys=[pickup_zone_id])
    drop_zone = relationship("Zone", back_populates="drop_rates", foreign_keys=[drop_zone_id])
    
    __table_args__ = (
        CheckConstraint("min_weight_kg >= 0", name="ck_min_weight_positive"),
        CheckConstraint("max_weight_kg IS NULL OR max_weight_kg > min_weight_kg", name="ck_max_weight_greater"),
        CheckConstraint("base_charge >= 0", name="ck_base_charge_positive"),
        CheckConstraint("per_kg_charge >= 0", name="ck_per_kg_charge_positive"),
        Index("ix_rate_rules_lookup", "rate_card_id", "pickup_zone_id", "drop_zone_id", "min_weight_kg"),
    )


class CODSurcharge(Base):
    __tablename__ = "cod_surcharges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_card_id = Column(UUID(as_uuid=True), ForeignKey("rate_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    min_order_value = Column(Numeric(10, 2), nullable=False, default=0)
    max_order_value = Column(Numeric(10, 2), nullable=True)
    surcharge_percentage = Column(Numeric(5, 2), nullable=False)  # e.g., 2.5 for 2.5%
    min_surcharge = Column(Numeric(10, 2), nullable=False, default=0)
    max_surcharge = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    rate_card = relationship("RateCard", back_populates="cod_surcharges")
    
    __table_args__ = (
        CheckConstraint("surcharge_percentage >= 0 AND surcharge_percentage <= 100", name="ck_surcharge_percentage"),
        CheckConstraint("min_surcharge >= 0", name="ck_min_surcharge_positive"),
        CheckConstraint("max_surcharge IS NULL OR max_surcharge >= min_surcharge", name="ck_max_surcharge_greater"),
        CheckConstraint("max_order_value IS NULL OR max_order_value > min_order_value", name="ck_max_order_value_greater"),
        Index("ix_cod_surcharge_lookup", "rate_card_id", "min_order_value", "is_active"),
    )


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Pickup details
    pickup_address = Column(Text, nullable=False)
    pickup_pincode = Column(String(10), nullable=False, index=True)
    pickup_city = Column(String(100), nullable=True)
    pickup_state = Column(String(100), nullable=True)
    pickup_zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True, index=True)
    
    # Drop details
    drop_address = Column(Text, nullable=False)
    drop_pincode = Column(String(10), nullable=False, index=True)
    drop_city = Column(String(100), nullable=True)
    drop_state = Column(String(100), nullable=True)
    drop_zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True, index=True)
    
    # Package details
    length_cm = Column(Numeric(10, 2), nullable=False)
    breadth_cm = Column(Numeric(10, 2), nullable=False)
    height_cm = Column(Numeric(10, 2), nullable=False)
    actual_weight_kg = Column(Numeric(10, 3), nullable=False)
    volumetric_weight_kg = Column(Numeric(10, 3), nullable=False)
    billable_weight_kg = Column(Numeric(10, 3), nullable=False)
    
    # Order classification
    order_type = Column(Enum(OrderType), nullable=False, index=True)
    payment_type = Column(Enum(PaymentType), nullable=False, index=True)
    zone_type = Column(Enum(ZoneType), nullable=False)
    
    # Pricing (snapshot at creation)
    base_charge = Column(Numeric(10, 2), nullable=False)
    cod_surcharge = Column(Numeric(10, 2), nullable=False, default=0)
    total_charge = Column(Numeric(10, 2), nullable=False)
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False, index=True)
    failure_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    agent = relationship("User", back_populates="assigned_orders", foreign_keys=[agent_id])
    pickup_zone = relationship("Zone", foreign_keys=[pickup_zone_id])
    drop_zone = relationship("Zone", foreign_keys=[drop_zone_id])
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.created_at")
    delivery_attempts = relationship("DeliveryAttempt", back_populates="order", cascade="all, delete-orphan")
    assignment = relationship("DeliveryAssignment", back_populates="order", uselist=False)
    reschedule_requests = relationship("RescheduleRequest", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("actual_weight_kg > 0", name="ck_actual_weight_positive"),
        CheckConstraint("billable_weight_kg >= actual_weight_kg", name="ck_billable_weight"),
        CheckConstraint("total_charge >= 0", name="ck_total_charge_positive"),
        Index("ix_orders_customer_status", "customer_id", "status"),
        Index("ix_orders_agent_status", "agent_id", "status"),
        Index("ix_orders_created_status", "created_at", "status"),
    )


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(OrderStatus), nullable=True)
    new_status = Column(Enum(OrderStatus), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    actor_role = Column(Enum(UserRole), nullable=False)
    reason = Column(Text, nullable=True)
    context_data = Column(JSON, nullable=True)  # Additional context (location, etc.)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    order = relationship("Order", back_populates="status_history")
    actor = relationship("User", back_populates="status_history")
    
    __table_args__ = (
        Index("ix_status_history_order_created", "order_id", "created_at"),
    )


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True, index=True)
    status = Column(Enum(AgentStatus), default=AgentStatus.OFFLINE, nullable=False, index=True)
    max_concurrent_deliveries = Column(Integer, default=3, nullable=False)
    current_deliveries_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="agent_profile")
    zone = relationship("Zone", back_populates="agents")
    location = relationship("AgentLocation", back_populates="agent", uselist=False)
    assignments = relationship("DeliveryAssignment", back_populates="agent")


class AgentLocation(Base):
    __tablename__ = "agent_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    accuracy_meters = Column(Integer, nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="location")
    zone = relationship("Zone")


class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Admin who manually assigned
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    is_auto_assigned = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="assignment")
    agent = relationship("Agent", back_populates="assignments")
    assigned_by_user = relationship("User")


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    status = Column(Enum(DeliveryAttemptStatus), default=DeliveryAttemptStatus.PENDING, nullable=False)
    failure_reason = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    proof_of_delivery = Column(Text, nullable=True)  # Photo URL, signature, etc.
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="delivery_attempts")
    agent = relationship("Agent")
    
    __table_args__ = (
        UniqueConstraint("order_id", "attempt_number", name="uq_order_attempt"),
        Index("ix_delivery_attempts_order_agent", "order_id", "agent_id"),
    )


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # email, sms
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, sent, failed
    external_id = Column(String(100), nullable=True)  # Provider message ID
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    order = relationship("Order")
    
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_order_type", "order_id", "type"),
    )


class RescheduleRequest(Base):
    __tablename__ = "reschedule_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preferred_date = Column(DateTime, nullable=False)
    preferred_time_slot = Column(String(50), nullable=True)  # morning, afternoon, evening
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    new_delivery_attempt_id = Column(UUID(as_uuid=True), ForeignKey("delivery_attempts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="reschedule_requests")
    customer = relationship("User", foreign_keys=[customer_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    new_delivery_attempt = relationship("DeliveryAttempt")
    
    __table_args__ = (
        Index("ix_reschedule_order_status", "order_id", "status"),
    )