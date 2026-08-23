from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, require_customer
from app.models import OrderStatus, User, UserRole
from app.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
    OrderStatusUpdate,
    OrderUpdate,
)
from app.services.order import OrderService, get_order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/quote")
async def get_quote(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(require_customer)
):
    """Get price quote before order confirmation"""
    try:
        # Use pricing engine directly for quote
        from app.services.pricing import PricingEngine
        pricing_engine = PricingEngine(order_service.db)

        from app.schemas.pricing import QuoteRequest
        quote_request = QuoteRequest(
            length_cm=order_data.length_cm,
            breadth_cm=order_data.breadth_cm,
            height_cm=order_data.height_cm,
            actual_weight_kg=order_data.actual_weight_kg,
            order_type=order_data.order_type,
            payment_type=order_data.payment_type,
            pickup_pincode=order_data.pickup_pincode,
            pickup_city=order_data.pickup_city,
            pickup_state=order_data.pickup_state,
            drop_pincode=order_data.drop_pincode,
            drop_city=order_data.drop_city,
            drop_state=order_data.drop_state,
            order_value=order_data.order_value
        )

        result = await pricing_engine.calculate_quote(quote_request)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(require_customer)
):
    """Create a new order (server-side price recalculation)"""
    try:
        order = await order_service.create_order(current_user.id, order_data)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: Optional[OrderStatus] = None,
    order_type: Optional[str] = None,
    payment_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """List orders with filters (customers see only their orders)"""
    customer_id = current_user.id if current_user.role == UserRole.CUSTOMER else None
    agent_id = current_user.id if current_user.role == UserRole.AGENT else None

    # Admin can filter by customer_id and agent_id via query params
    if current_user.role == UserRole.ADMIN:
        customer_id = None
        agent_id = None

    orders, total = await order_service.list_orders(
        customer_id=customer_id,
        agent_id=agent_id,
        status=status,
        order_type=order_type,
        payment_type=payment_type,
        skip=skip,
        limit=limit
    )

    return OrderListResponse(
        orders=orders,
        total=total,
        page=skip // limit + 1,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order details"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Authorization check
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.AGENT and order.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return order


@router.get("/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order by order number"""
    order = await order_service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.AGENT and order.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Update order status"""
    # Check permissions
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER:
        # Customers can only cancel their own orders
        if order.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if status_update.status != OrderStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Customers can only cancel orders")
    elif current_user.role == UserRole.AGENT:
        # Agents can update status of assigned orders
        if order.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Agents cannot cancel
        if status_update.status == OrderStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Agents cannot cancel orders")

    try:
        updated_order = await order_service.update_order_status(
            order_id=order_id,
            new_status=status_update.status,
            actor_id=current_user.id,
            actor_role=current_user.role,
            reason=status_update.reason
        )
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}/tracking", response_model=List[OrderStatusHistoryResponse])
async def get_order_tracking(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order tracking history"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.AGENT and order.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    history = await order_service.get_status_history(order_id)
    return history


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_update: OrderUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(require_customer)
):
    """Update order details (customer only, before pickup)"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if order.status != OrderStatus.CREATED:
        raise HTTPException(status_code=400, detail="Can only update orders in CREATED status")

    # Recalculate price if address or weight changed
    from app.schemas.pricing import PricingRequest
    pricing_request = PricingRequest(
        length_cm=order.length_cm,
        breadth_cm=order.breadth_cm,
        height_cm=order.height_cm,
        actual_weight_kg=order.actual_weight_kg,
        order_type=order.order_type,
        payment_type=order.payment_type,
        pickup_zone_id=order.pickup_zone_id,
        drop_zone_id=order.drop_zone_id,
        order_value=order.order_value
    )

    pricing_engine = order_service.pricing_engine
    pricing_result = await pricing_engine.calculate_price(pricing_request)

    if not pricing_result["success"]:
        raise HTTPException(status_code=400, detail=pricing_result["error"])

    breakdown = pricing_result["breakdown"]

    # Update fields
    if order_update.pickup_address:
        order.pickup_address = order_update.pickup_address
    if order_update.drop_address:
        order.drop_address = order_update.drop_address
    if order_update.order_value is not None:
        order.order_value = order_update.order_value

    order.base_charge = breakdown["base_charge"]
    order.cod_surcharge = breakdown["cod_surcharge"]
    order.total_charge = breakdown["total_charge"]

    await order_service.db.commit()
    await order_service.db.refresh(order)

    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Cancel order (customer)"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if order.status not in [OrderStatus.CREATED, OrderStatus.PICKED_UP]:
        raise HTTPException(status_code=400, detail="Cannot cancel order in current status")

    await order_service.update_order_status(
        order_id=order_id,
        new_status=OrderStatus.CANCELLED,
        actor_id=current_user.id,
        actor_role=current_user.role,
        reason="Cancelled by customer"
    )
