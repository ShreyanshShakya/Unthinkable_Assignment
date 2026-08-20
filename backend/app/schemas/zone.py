from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.models import ZoneType


class ZoneBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)
    description: Optional[str] = None


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ZoneResponse(ZoneBase):
    id: UUID
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ZoneAreaBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=1, max_length=10)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)


class ZoneAreaCreate(ZoneAreaBase):
    zone_id: UUID


class ZoneAreaUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    pincode: Optional[str] = Field(default=None, min_length=1, max_length=10)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class ZoneAreaResponse(ZoneAreaBase):
    id: UUID
    zone_id: UUID
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RateCardBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    order_type: str
    zone_type: ZoneType


class RateCardCreate(RateCardBase):
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class RateCardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class RateCardResponse(RateCardBase):
    id: UUID
    is_active: bool
    effective_from: str
    effective_to: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RateCardRuleBase(BaseModel):
    pickup_zone_id: UUID
    drop_zone_id: UUID
    min_weight_kg: float = Field(ge=0)
    max_weight_kg: Optional[float] = Field(default=None, ge=0)
    base_charge: float = Field(ge=0)
    per_kg_charge: float = Field(ge=0, default=0)


class RateCardRuleCreate(RateCardRuleBase):
    rate_card_id: UUID


class RateCardRuleUpdate(BaseModel):
    min_weight_kg: Optional[float] = Field(default=None, ge=0)
    max_weight_kg: Optional[float] = Field(default=None, ge=0)
    base_charge: Optional[float] = Field(default=None, ge=0)
    per_kg_charge: Optional[float] = Field(default=None, ge=0)


class RateCardRuleResponse(RateCardRuleBase):
    id: UUID
    rate_card_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CODSurchargeBase(BaseModel):
    min_order_value: float = Field(ge=0, default=0)
    max_order_value: Optional[float] = Field(default=None, ge=0)
    surcharge_percentage: float = Field(ge=0, le=100)
    min_surcharge: float = Field(ge=0, default=0)
    max_surcharge: Optional[float] = Field(default=None, ge=0)


class CODSurchargeCreate(CODSurchargeBase):
    rate_card_id: UUID


class CODSurchargeUpdate(BaseModel):
    min_order_value: Optional[float] = Field(default=None, ge=0)
    max_order_value: Optional[float] = Field(default=None, ge=0)
    surcharge_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    min_surcharge: Optional[float] = Field(default=None, ge=0)
    max_surcharge: Optional[float] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class CODSurchargeResponse(CODSurchargeBase):
    id: UUID
    rate_card_id: UUID
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True