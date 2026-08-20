from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import (
    Order, DeliveryAttempt, RescheduleRequest, OrderStatusHistory,
    OrderStatus, DeliveryAttemptStatus, UserRole, User, Agent
)
from app.services.order import OrderService
from app.services.notification import NotificationService
from app.db.session import get_db


class FailedDeliveryService:
    """Service for handling failed deliveries and rescheduling"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_service = OrderService(db)
        self.notification_service = NotificationService(db)
    
    async def mark_delivery_failed(
        self, 
        order_id: UUID, 
        agent_id: UUID, 
        failure_reason: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Order:
        """Mark order as failed delivery"""
        order = await self.order_service.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.agent_id != agent_id:
            raise ValueError("Not assigned to this agent")
        
        if order.status != OrderStatus.OUT_FOR_DELIVERY:
            raise ValueError("Order must be OUT_FOR_DELIVERY to mark as failed")
        
        # Update order status
        order = await self.order_service.update_order_status(
            order_id=order_id,
            new_status=OrderStatus.FAILED,
            actor_id=agent_id,
            actor_role=UserRole.AGENT,
            reason=f"Delivery failed: {failure_reason}"
        )
        
        # Create delivery attempt record
        attempt_number = await self._get_next_attempt_number(order_id)
        attempt = DeliveryAttempt(
            id=uuid4(),
            order_id=order_id,
            agent_id=agent_id,
            attempt_number=attempt_number,
            status=DeliveryAttemptStatus.FAILED,
            failure_reason=failure_reason,
            latitude=latitude,
            longitude=longitude,
            started_at=order.updated_at,  # Approximate
            completed_at=datetime.utcnow(),
        )
        self.db.add(attempt)
        
        # Release agent
        result = await self.db.execute(select(Agent).where(Agent.user_id == agent_id))
        agent = result.scalar_one_or_none()
        if agent:
            agent.current_deliveries_count = max(0, agent.current_deliveries_count - 1)
            if agent.current_deliveries_count == 0:
                agent.status = "available"  # AgentStatus.AVAILABLE
        
        await self.db.commit()
        
        # Notify customer
        await self._notify_customer_failed_delivery(order, failure_reason, attempt.id)
        
        return order
    
    async def _get_next_attempt_number(self, order_id: UUID) -> int:
        """Get next attempt number for order"""
        result = await self.db.execute(
            select(func.max(DeliveryAttempt.attempt_number))
            .where(DeliveryAttempt.order_id == order_id)
        )
        max_attempt = result.scalar() or 0
        return max_attempt + 1
    
    async def _notify_customer_failed_delivery(self, order: Order, failure_reason: str, attempt_id: UUID):
        """Send failure notification to customer"""
        customer_result = await self.db.execute(
            select(User).where(User.id == order.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if not customer:
            return
        
        # Create notification
        await self.notification_service.create_notification(
            user_id=customer.id,
            order_id=order.id,
            type="email",
            subject=f"Delivery Failed - Order {order.order_number}",
            message=f"""
            Your delivery for order {order.order_number} has failed.
            
            Reason: {failure_reason}
            
            You can reschedule the delivery by visiting your order details page.
            A new delivery attempt will be scheduled once you select a preferred date.
            """
        )
        
        # Also send SMS if phone available
        if customer.phone:
            await self.notification_service.create_notification(
                user_id=customer.id,
                order_id=order.id,
                type="sms",
                subject=None,
                message=f"Delivery failed for order {order.order_number}. Reason: {failure_reason}. Please reschedule in the app."
            )
    
    async def create_reschedule_request(
        self, 
        order_id: UUID, 
        customer_id: UUID, 
        preferred_date: datetime,
        preferred_time_slot: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RescheduleRequest:
        """Create a reschedule request for a failed delivery"""
        order = await self.order_service.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.customer_id != customer_id:
            raise ValueError("Not authorized for this order")
        
        if order.status != OrderStatus.FAILED:
            raise ValueError("Can only reschedule failed deliveries")
        
        # Validate preferred date is in the future
        if preferred_date <= datetime.utcnow():
            raise ValueError("Preferred date must be in the future")
        
        # Check for existing pending reschedule request
        result = await self.db.execute(
            select(RescheduleRequest)
            .where(RescheduleRequest.order_id == order_id)
            .where(RescheduleRequest.status == "pending")
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("Reschedule request already pending")
        
        reschedule = RescheduleRequest(
            id=uuid4(),
            order_id=order_id,
            customer_id=customer_id,
            preferred_date=preferred_date,
            preferred_time_slot=preferred_time_slot,
            reason=reason,
            status="pending",
        )
        self.db.add(reschedule)
        await self.db.commit()
        await self.db.refresh(reschedule)
        
        return reschedule
    
    async def approve_reschedule(
        self, 
        reschedule_id: UUID, 
        admin_id: UUID,
        new_agent_id: Optional[UUID] = None
    ) -> RescheduleRequest:
        """Approve reschedule request and create new delivery attempt"""
        result = await self.db.execute(
            select(RescheduleRequest).where(RescheduleRequest.id == reschedule_id)
        )
        reschedule = result.scalar_one_or_none()
        if not reschedule:
            raise ValueError("Reschedule request not found")
        
        if reschedule.status != "pending":
            raise ValueError("Reschedule request already processed")
        
        order = await self.order_service.get_order(reschedule.order_id)
        if not order:
            raise ValueError("Order not found")
        
        # Update reschedule request
        reschedule.status = "approved"
        reschedule.approved_by = admin_id
        reschedule.approved_at = datetime.utcnow()
        
        # Create new delivery attempt
        attempt_number = await self._get_next_attempt_number(order.id)
        
        # Find agent - use new_agent_id or auto-assign
        agent_id = new_agent_id
        if not agent_id:
            # Auto-assign to available agent in pickup zone
            agent = await self._find_available_agent(order.pickup_zone_id)
            if agent:
                agent_id = agent.id
        
        if not agent_id:
            raise ValueError("No available agents for rescheduled delivery")
        
        new_attempt = DeliveryAttempt(
            id=uuid4(),
            order_id=order.id,
            agent_id=agent_id,
            attempt_number=attempt_number,
            status=DeliveryAttemptStatus.PENDING,
        )
        self.db.add(new_attempt)
        
        reschedule.new_delivery_attempt_id = new_attempt.id
        
        # Update order status back to CREATED for new attempt
        order.status = OrderStatus.CREATED
        order.agent_id = None
        
        # Assign agent
        agent_result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one_or_none()
        if agent:
            order.agent_id = agent.user_id
            agent.current_deliveries_count += 1
            agent.status = "busy"  # AgentStatus.BUSY
        
        # Create assignment
        from app.models import DeliveryAssignment
        assignment = DeliveryAssignment(
            id=uuid4(),
            order_id=order.id,
            agent_id=agent_id,
            assigned_by=admin_id,
            is_auto_assigned=new_agent_id is None,
        )
        self.db.add(assignment)
        
        # Create status history
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=OrderStatus.FAILED,
            new_status=OrderStatus.CREATED,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
            reason=f"Rescheduled for {reschedule.preferred_date.isoformat()}"
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(reschedule)
        
        # Notify customer
        await self._notify_customer_rescheduled(order, reschedule)
        
        return reschedule
    
    async def _find_available_agent(self, zone_id: Optional[UUID]) -> Optional[Agent]:
        """Find available agent in zone"""
        query = select(Agent).where(
            Agent.is_active == True,
            Agent.current_deliveries_count < Agent.max_concurrent_deliveries,
            Agent.status == "available"  # AgentStatus.AVAILABLE
        )
        if zone_id:
            query = query.where(Agent.zone_id == zone_id)
        
        result = await self.db.execute(
            query.order_by(Agent.current_deliveries_count.asc()).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def _notify_customer_rescheduled(self, order: Order, reschedule: RescheduleRequest):
        """Notify customer of approved reschedule"""
        customer_result = await self.db.execute(
            select(User).where(User.id == order.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if not customer:
            return
        
        await self.notification_service.create_notification(
            user_id=customer.id,
            order_id=order.id,
            type="email",
            subject=f"Delivery Rescheduled - Order {order.order_number}",
            message=f"""
            Your delivery for order {order.order_number} has been rescheduled.
            
            New delivery date: {reschedule.preferred_date.strftime('%Y-%m-%d')}
            Time slot: {reschedule.preferred_time_slot or 'As scheduled'}
            
            A new delivery agent will be assigned.
            """
        )
        
        if customer.phone:
            await self.notification_service.create_notification(
                user_id=customer.id,
                order_id=order.id,
                type="sms",
                subject=None,
                message=f"Order {order.order_number} rescheduled for {reschedule.preferred_date.strftime('%Y-%m-%d')}."
            )
    
    async def reject_reschedule(self, reschedule_id: UUID, admin_id: UUID, reason: str) -> RescheduleRequest:
        """Reject reschedule request"""
        result = await self.db.execute(
            select(RescheduleRequest).where(RescheduleRequest.id == reschedule_id)
        )
        reschedule = result.scalar_one_or_none()
        if not reschedule:
            raise ValueError("Reschedule request not found")
        
        reschedule.status = "rejected"
        reschedule.approved_by = admin_id
        reschedule.approved_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(reschedule)
        
        return reschedule
    
    async def list_reschedule_requests(
        self, 
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[RescheduleRequest], int]:
        """List reschedule requests with filters"""
        query = select(RescheduleRequest)
        
        if order_id:
            query = query.where(RescheduleRequest.order_id == order_id)
        if customer_id:
            query = query.where(RescheduleRequest.customer_id == customer_id)
        if status:
            query = query.where(RescheduleRequest.status == status)
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        query = query.order_by(RescheduleRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return requests, total
    
    async def get_delivery_attempts(self, order_id: UUID) -> List[DeliveryAttempt]:
        """Get all delivery attempts for an order"""
        result = await self.db.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.order_id == order_id)
            .order_by(DeliveryAttempt.attempt_number.asc())
        )
        return result.scalars().all()


async def get_failed_delivery_service(db: AsyncSession = Depends(get_db)) -> FailedDeliveryService:
    from fastapi import Depends
    from app.db.session import get_db
    return FailedDeliveryService(db)