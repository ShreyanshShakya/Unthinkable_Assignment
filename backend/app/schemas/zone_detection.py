from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ZoneInfo(BaseModel):
    id: UUID
    name: str
    code: str


class ZoneDetectionRequest(BaseModel):
    pickup_pincode: str = Field(min_length=1, max_length=10)
    pickup_city: Optional[str] = Field(default=None, max_length=100)
    pickup_state: Optional[str] = Field(default=None, max_length=100)
    drop_pincode: str = Field(min_length=1, max_length=10)
    drop_city: Optional[str] = Field(default=None, max_length=100)
    drop_state: Optional[str] = Field(default=None, max_length=100)


class ZoneDetectionResponse(BaseModel):
    pickup_zone: Optional[ZoneInfo] = None
    drop_zone: Optional[ZoneInfo] = None
    zone_type: Optional[str] = None


class ZoneByPincodeRequest(BaseModel):
    pincode: str = Field(min_length=1, max_length=10)


class ZoneByPincodeResponse(BaseModel):
    zone: Optional[ZoneInfo] = None
    found: bool
