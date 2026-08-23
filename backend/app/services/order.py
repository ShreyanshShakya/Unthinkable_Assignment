from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models import (
    Order, OrderStatusHistory, User, Zone, ZoneArea, 
    OrderStatus, OrderType, PaymentType, ZoneType, UserRole
)
from app.db.session import get_db
from app.services.pricing import PricingEngine
from app.services.zone_detection import ZoneDetectionService
from app.services.notification import NotificationService


class OrderService:
    """Service for order management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pricing_engine = PricingEngine(db)
        self.zone_service = ZoneDetectionService(db)
    
    def generate_order_number(self) -> str:
        """Generate unique order number"""
        import random
        return f"ORD{datetime.utcnow().strftime('%Y%m%d')}{random.randint(10000, 99999)}"
    
    async def create_order(self, customer_id: UUID, order_data) -> Order:
        """Create a new order with server-side price calculation"""
        # Detect zones if not provided
        pickup_zone_id = order_data.pickup_zone_id
        drop_zone_id = order_data.drop_zone_id
        
        if not pickup_zone_id or not drop_zone_id:
            pickup_zone, drop_zone = await self.zone_service.get_pickup_drop_zones(
                pickup_pincode=order_data.pickup_pincode,
                pickup_city=order_data.pickup_city,
                pickup_state=order_data.pickup_state,
                drop_pincode=order_data.drop_pincode,
                drop_city=order_data.drop_city,
                drop_state=order_data.drop_state
            )
            
            if not pickup_zone:
                raise ValueError(f"Pickup zone not found for pincode {order_data.pickup_pincode}")
            if not drop_zone:
                raise ValueError(f"Drop zone not found for pincode {order_data.drop_pincode}")
            
            pickup_zone_id = pickup_zone_id or pickup_zone.id
            drop_zone_id = drop_zone_id or drop_zone.id
        
        # Calculate pricing
        from app.schemas.pricing import PricingRequest
        pricing_request = PricingRequest(
            length_cm=order_data.length_cm,
            breadth_cm=order_data.breadth_cm,
            height_cm=order_data.height_cm,
            actual_weight_kg=order_data.actual_weight_kg,
            order_type=order_data.order_type,
            payment_type=order_data.payment_type,
            pickup_zone_id=pickup_zone_id,
            drop_zone_id=drop_zone_id,
            order_value=order_data.order_value
        )
        
        pricing_result = await self.pricing_engine.calculate_price(pricing_request)
        
        if not pricing_result["success"]:
            raise ValueError(pricing_result["error"])
        
        breakdown = pricing_result["breakdown"]
        
        # Create order
        order = Order(
            id=uuid4(),
            order_number=self.generate_order_number(),
            customer_id=customer_id,
            
            pickup_address=order_data.pickup_address,
            pickup_pincode=order_data.pickup_pincode,
            pickup_city=order_data.pickup_city,
            pickup_state=order_data.pickup_state,
            pickup_zone_id=pickup_zone_id,
            
            drop_address=order_data.drop_address,
            drop_pincode=order_data.drop_pincode,
            drop_city=order_data.drop_city,
            drop_state=order_data.drop_state,
            drop_zone_id=drop_zone_id,
            
            length_cm=order_data.length_cm,
            breadth_cm=order_data.breadth_cm,
            height_cm=order_data.height_cm,
            actual_weight_kg=order_data.actual_weight_kg,
            volumetric_weight_kg=breakdown["volumetric_weight_kg"],
            billable_weight_kg=breakdown["billable_weight_kg"],
            
            order_type=order_data.order_type,
            payment_type=order_data.payment_type,
            zone_type=breakdown["zone_type"],
            
            base_charge=breakdown["base_charge"],
            cod_surcharge=breakdown["cod_surcharge"],
            total_charge=breakdown["total_charge"],
            
            status=OrderStatus.CREATED,
        )
        
        self.db.add(order)
        
        # Create initial status history
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=None,
            new_status=OrderStatus.CREATED,
            actor_id=customer_id,
            actor_role=UserRole.CUSTOMER,
            reason="Order created"
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # Send order creation notification
        notification_service = NotificationService(self.db)
        await notification_service.notify_order_status_change(
            order_id=order.id,
            old_status=None,
            new_status=OrderStatus.CREATED.value,
            actor_role=UserRole.CUSTOMER.value
        )
        
        return order
    
    async def get_order(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID with relationships"""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.agent),
                selectinload(Order.pickup_zone),
                selectinload(Order.drop_zone)
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()
    
    async def list_orders(
        self, 
        customer_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[OrderStatus] = None,
        order_type: Optional[OrderType] = None,
        payment_type: Optional[PaymentType] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Order], int]:
        """List orders with filters"""
        query = select(Order)
        
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        if agent_id:
            query = query.where(Order.agent_id == agent_id)
        if status:
            query = query.where(Order.status == status)
        if order_type:
            query = query.where(Order.order_type == order_type)
        if payment_type:
            query = query.where(Order.payment_type == payment_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return orders, total
    
    async def update_order_status(
        self, 
        order_id: UUID, 
        new_status: OrderStatus, 
        actor_id: UUID, 
        actor_role: UserRole,
        reason: Optional[str] = None
    ) -> Optional[Order]:
        """Update order status with validation and history"""
        order = await self.get_order(order_id)
        if not order:
            return None
        
        # Validate transition
        if not self._is_valid_transition(order.status, new_status):
            raise ValueError(f"Invalid status transition from {order.status.value} to {new_status.value}")
        
        old_status = order.status
        order.status = new_status
        
        # Update timestamps
        if new_status == OrderStatus.PICKED_UP and not order.picked_up_at:
            order.picked_up_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = datetime.utcnow()
        
        # Create status history
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            actor_id=actor_id,
            actor_role=actor_role,
            reason=reason
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # Send notifications
        notification_service = NotificationService(self.db)
        await notification_service.notify_order_status_change(
            order_id=order.id,
            old_status=old_status.value if old_status else None,
            new_status=new_status.value,
            actor_role=actor_role.value
        )
        
        return order
    
    def _is_valid_transition(self, current: OrderStatus, new: OrderStatus) -> bool:
        """Validate status transition"""
        valid_transitions = {
            OrderStatus.CREATED: [OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
            OrderStatus.ASSIGNED: [OrderStatus.PICKED_UP, OrderStatus.CANCELLED],
            OrderStatus.PICKED_UP: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
            OrderStatus.IN_TRANSIT: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.FAILED],
            OrderStatus.FAILED: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }
        return new in valid_transitions.get(current, [])
    
    async def get_status_history(self, order_id: UUID) -> List[OrderStatusHistory]:
        """Get order status history"""
        result = await self.db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.created_at.asc())
        )
        return result.scalars().all()
    
    async def admin_override_status(
        self, 
        order_id: UUID, 
        new_status: OrderStatus, 
        admin_id: UUID, 
        reason: str
    ) -> Optional[Order]:
        """Admin status override (bypasses transition validation)"""
        order = await self.get_order(order_id)
        if not order:
            return None
        
        old_status = order.status
        order.status = new_status
        
        if new_status == OrderStatus.PICKED_UP and not order.picked_up_at:
            order.picked_up_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = datetime.utcnow()
        
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
            reason=f"Admin override: {reason}"
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # Send notifications
        notification_service = NotificationService(self.db)
        await notification_service.notify_order_status_change(
            order_id=order.id,
            old_status=old_status.value if old_status else None,
            new_status=new_status.value,
            actor_role=UserRole.ADMIN.value
        )
        
        return order


async def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    from fastapi import Depends
    from app.db.session import get_db
    return OrderService(db)