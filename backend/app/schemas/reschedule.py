from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models import DeliveryAttemptStatus


class RescheduleRequestCreate(BaseModel):
    preferred_date: datetime
    preferred_time_slot: Optional[str] = Field(default=None, max_length=50)  # morning, afternoon, evening
    reason: Optional[str] = None


class RescheduleRequestUpdate(BaseModel):
    status: Optional[str] = None  # pending, approved, rejected
    approved_by: Optional[UUID] = None


class RescheduleRequestResponse(BaseModel):
    id: UUID
    order_id: UUID
    customer_id: UUID
    preferred_date: datetime
    preferred_time_slot: Optional[str]
    reason: Optional[str]
    status: str
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    new_delivery_attempt_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeliveryAttemptCreate(BaseModel):
    order_id: UUID
    agent_id: UUID
    attempt_number: int
    status: DeliveryAttemptStatus = DeliveryAttemptStatus.PENDING


class DeliveryAttemptUpdate(BaseModel):
    status: Optional[DeliveryAttemptStatus] = None
    failure_reason: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    proof_of_delivery: Optional[str] = None


class DeliveryAttemptResponse(BaseModel):
    id: UUID
    order_id: UUID
    agent_id: UUID
    attempt_number: int
    status: DeliveryAttemptStatus
    failure_reason: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    proof_of_delivery: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FailedDeliveryNotification(BaseModel):
    order_id: UUID
    order_number: str
    failure_reason: str
    failed_at: datetime
    reschedule_url: str