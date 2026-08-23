from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, require_admin, require_agent, require_customer
from app.models import User, UserRole
from app.schemas.reschedule import (
    DeliveryAttemptResponse,
    RescheduleRequestCreate,
    RescheduleRequestResponse,
)
from app.services.failed_delivery import FailedDeliveryService, get_failed_delivery_service

router = APIRouter(prefix="/failed-deliveries", tags=["failed-deliveries"])


@router.post("/{order_id}/mark-failed")
async def mark_delivery_failed(
    order_id: UUID,
    failure_reason: str,
    latitude: Optional[float] = Query(default=None, ge=-90, le=90),
    longitude: Optional[float] = Query(default=None, ge=-180, le=180),
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(require_agent)
):
    """Mark delivery as failed (agent only)"""
    try:
        order = await failed_service.mark_delivery_failed(
            order_id=order_id,
            agent_id=current_user.id,
            failure_reason=failure_reason,
            latitude=latitude,
            longitude=longitude
        )
        return {
            "success": True,
            "order_id": str(order.id),
            "order_number": order.order_number,
            "status": order.status.value,
            "message": "Delivery marked as failed. Customer notified."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/reschedule", response_model=RescheduleRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_reschedule_request(
    order_id: UUID,
    reschedule_data: RescheduleRequestCreate,
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(require_customer)
):
    """Create reschedule request for failed delivery (customer only)"""
    try:
        reschedule = await failed_service.create_reschedule_request(
            order_id=order_id,
            customer_id=current_user.id,
            preferred_date=reschedule_data.preferred_date,
            preferred_time_slot=reschedule_data.preferred_time_slot,
            reason=reschedule_data.reason
        )
        return reschedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reschedule-requests", response_model=List[RescheduleRequestResponse])
async def list_reschedule_requests(
    order_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(get_current_user)
):
    """List reschedule requests"""
    customer_id = current_user.id if current_user.role == UserRole.CUSTOMER else None

    requests, total = await failed_service.list_reschedule_requests(
        order_id=order_id,
        customer_id=customer_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return requests


@router.get("/reschedule-requests/{reschedule_id}", response_model=RescheduleRequestResponse)
async def get_reschedule_request(
    reschedule_id: UUID,
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(get_current_user)
):
    """Get reschedule request details"""
    requests, _ = await failed_service.list_reschedule_requests()
    reschedule = next((r for r in requests if r.id == reschedule_id), None)
    if not reschedule:
        raise HTTPException(status_code=404, detail="Reschedule request not found")

    if current_user.role == UserRole.CUSTOMER and reschedule.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return reschedule


# Admin endpoints
@router.patch("/reschedule-requests/{reschedule_id}/approve", response_model=RescheduleRequestResponse)
async def approve_reschedule(
    reschedule_id: UUID,
    new_agent_id: Optional[UUID] = None,
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(require_admin)
):
    """Approve reschedule request (admin only)"""
    try:
        reschedule = await failed_service.approve_reschedule(
            reschedule_id=reschedule_id,
            admin_id=current_user.id,
            new_agent_id=new_agent_id
        )
        return reschedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/reschedule-requests/{reschedule_id}/reject", response_model=RescheduleRequestResponse)
async def reject_reschedule(
    reschedule_id: UUID,
    reason: str,
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(require_admin)
):
    """Reject reschedule request (admin only)"""
    try:
        reschedule = await failed_service.reject_reschedule(
            reschedule_id=reschedule_id,
            admin_id=current_user.id,
            reason=reason
        )
        return reschedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}/attempts", response_model=List[DeliveryAttemptResponse])
async def get_delivery_attempts(
    order_id: UUID,
    failed_service: FailedDeliveryService = Depends(get_failed_delivery_service),
    current_user: User = Depends(get_current_user)
):
    """Get all delivery attempts for an order"""
    order = await failed_service.order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.AGENT:
        # Check if agent was involved in any attempt
        attempts = await failed_service.get_delivery_attempts(order_id)
        agent_involved = any(a.agent_id == current_user.id for a in attempts)
        if not agent_involved:
            raise HTTPException(status_code=403, detail="Not authorized")

    attempts = await failed_service.get_delivery_attempts(order_id)
    return attempts
