from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models import OrderType, PaymentType, OrderStatus, OrderType, ZoneType


class OrderCreate(BaseModel):
    # Pickup details
    pickup_address: str = Field(min_length=5)
    pickup_pincode: str = Field(min_length=1, max_length=10)
    pickup_city: Optional[str] = Field(default=None, max_length=100)
    pickup_state: Optional[str] = Field(default=None, max_length=100)
    
    # Drop details
    drop_address: str = Field(min_length=5)
    drop_pincode: str = Field(min_length=1, max_length=10)
    drop_city: Optional[str] = Field(default=None, max_length=100)
    drop_state: Optional[str] = Field(default=None, max_length=100)
    
    # Package details
    length_cm: float = Field(gt=0)
    breadth_cm: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    actual_weight_kg: float = Field(gt=0)
    
    # Order classification
    order_type: OrderType
    payment_type: PaymentType
    order_value: float = Field(ge=0, default=0)  # For COD
    
    # Optional: customer can provide zone IDs if known
    pickup_zone_id: Optional[UUID] = None
    drop_zone_id: Optional[UUID] = None


class OrderUpdate(BaseModel):
    pickup_address: Optional[str] = None
    drop_address: Optional[str] = None
    order_value: Optional[float] = Field(default=None, ge=0)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    reason: Optional[str] = None


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    customer_id: UUID
    agent_id: Optional[UUID] = None
    
    pickup_address: str
    pickup_pincode: str
    pickup_city: Optional[str]
    pickup_state: Optional[str]
    pickup_zone_id: Optional[UUID]
    
    drop_address: str
    drop_pincode: str
    drop_city: Optional[str]
    drop_state: Optional[str]
    drop_zone_id: Optional[UUID]
    
    length_cm: float
    breadth_cm: float
    height_cm: float
    actual_weight_kg: float
    volumetric_weight_kg: float
    billable_weight_kg: float
    
    order_type: OrderType
    payment_type: PaymentType
    zone_type: ZoneType
    
    base_charge: float
    cod_surcharge: float
    total_charge: float
    
    status: OrderStatus
    failure_reason: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderStatusHistoryResponse(BaseModel):
    id: UUID
    order_id: UUID
    old_status: Optional[OrderStatus]
    new_status: OrderStatus
    actor_id: UUID
    actor_role: str
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    limit: int
    total_pages: int