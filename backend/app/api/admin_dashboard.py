from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import Agent, AgentStatus, Order, OrderStatus, OrderType, PaymentType, User
from app.schemas.order import OrderListResponse, OrderResponse, OrderStatusUpdate
from app.services.order import OrderService, get_order_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    now = datetime.utcnow()
    start_today = datetime(now.year, now.month, now.day)
    total_orders = await db.scalar(select(func.count(Order.id))) or 0
    active_orders = await db.scalar(select(func.count(Order.id)).where(Order.status.in_([
        OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY
    ]))) or 0
    delivered_today = await db.scalar(select(func.count(Order.id)).where(
        Order.status == OrderStatus.DELIVERED, Order.delivered_at >= start_today
    )) or 0
    revenue_today = await db.scalar(select(func.coalesce(func.sum(Order.total_charge), 0)).where(
        Order.status == OrderStatus.DELIVERED, Order.delivered_at >= start_today
    )) or 0
    total_agents = await db.scalar(select(func.count(Agent.id)).where(Agent.is_active == True)) or 0
    available_agents = await db.scalar(select(func.count(Agent.id)).where(
        Agent.is_active == True, Agent.status == AgentStatus.AVAILABLE
    )) or 0
    return {
        "total_orders": int(total_orders), "active_orders": int(active_orders),
        "delivered_today": int(delivered_today), "revenue_today": float(revenue_today),
        "total_agents": int(total_agents), "available_agents": int(available_agents),
    }


@router.get("/orders", response_model=OrderListResponse)
async def admin_list_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    order_type: Optional[OrderType] = None,
    payment_type: Optional[PaymentType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(Order).options(
        selectinload(Order.customer), selectinload(Order.agent),
        selectinload(Order.pickup_zone), selectinload(Order.drop_zone),
    )
    if status_filter is not None: query = query.where(Order.status == status_filter)
    if order_type is not None: query = query.where(Order.order_type == order_type)
    if payment_type is not None: query = query.where(Order.payment_type == payment_type)
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    result = await db.execute(query.order_by(Order.created_at.desc()).offset(skip).limit(limit))
    orders = result.scalars().all()
    return OrderListResponse(
        orders=orders, total=int(total), page=skip // limit + 1,
        limit=limit, total_pages=(int(total) + limit - 1) // limit,
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def admin_get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Order).options(
        selectinload(Order.customer), selectinload(Order.agent),
        selectinload(Order.pickup_zone), selectinload(Order.drop_zone),
    ).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(require_admin),
):
    order = await order_service.admin_override_status(
        order_id=order_id,
        new_status=status_update.status,
        admin_id=current_user.id,
        reason=status_update.reason or "Updated from admin dashboard",
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
