from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import AgentStatus


class AgentProfileCreate(BaseModel):
    employee_id: str = Field(min_length=1, max_length=50)
    zone_id: Optional[UUID] = None
    max_concurrent_deliveries: int = Field(default=3, ge=1, le=10)


class AgentProfileUpdate(BaseModel):
    zone_id: Optional[UUID] = None
    max_concurrent_deliveries: Optional[int] = Field(default=None, ge=1, le=10)
    is_active: Optional[bool] = None


class AgentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    employee_id: str
    zone_id: Optional[UUID]
    status: AgentStatus
    max_concurrent_deliveries: int
    current_deliveries_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # User info
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None

    class Config:
        from_attributes = True


class AgentLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: Optional[int] = Field(default=None, ge=0)


class AgentLocationResponse(BaseModel):
    id: UUID
    agent_id: UUID
    latitude: float
    longitude: float
    accuracy_meters: Optional[int]
    zone_id: Optional[UUID]
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentAvailabilityUpdate(BaseModel):
    status: AgentStatus


class AssignmentRequest(BaseModel):
    order_id: UUID
    agent_id: Optional[UUID] = None  # If None, auto-assign nearest


class AssignmentResponse(BaseModel):
    id: UUID
    order_id: UUID
    agent_id: UUID
    assigned_by: Optional[UUID]
    assigned_at: datetime
    accepted_at: Optional[datetime]
    is_auto_assigned: bool

    class Config:
        from_attributes = True


class NearbyAgent(BaseModel):
    agent_id: UUID
    agent_name: str
    agent_phone: Optional[str]
    distance_km: float
    current_deliveries: int
    max_deliveries: int
    status: AgentStatus

    class Config:
        from_attributes = True
