from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import OrderType, PaymentType, ZoneType


class PricingRequest(BaseModel):
    length_cm: float = Field(gt=0)
    breadth_cm: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    actual_weight_kg: float = Field(gt=0)
    order_type: OrderType
    payment_type: PaymentType
    pickup_zone_id: UUID
    drop_zone_id: UUID
    order_value: float = Field(ge=0, default=0)  # For COD surcharge calculation


class PricingBreakdown(BaseModel):
    volumetric_weight_kg: float
    billable_weight_kg: float
    zone_type: ZoneType
    rate_card_id: Optional[UUID] = None
    base_charge: float
    cod_surcharge: float
    total_charge: float
    applied_rule: Optional[str] = None
    applied_cod_surcharge: Optional[str] = None


class PricingResponse(BaseModel):
    success: bool
    breakdown: Optional[PricingBreakdown] = None
    error: Optional[str] = None


class QuoteRequest(BaseModel):
    length_cm: float = Field(gt=0)
    breadth_cm: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    actual_weight_kg: float = Field(gt=0)
    order_type: OrderType
    payment_type: PaymentType
    pickup_pincode: str
    pickup_city: Optional[str] = None
    pickup_state: Optional[str] = None
    drop_pincode: str
    drop_city: Optional[str] = None
    drop_state: Optional[str] = None
    order_value: float = Field(ge=0, default=0)


class QuoteResponse(BaseModel):
    success: bool
    pricing: Optional[PricingBreakdown] = None
    pickup_zone: Optional[dict] = None
    drop_zone: Optional[dict] = None
    error: Optional[str] = None
