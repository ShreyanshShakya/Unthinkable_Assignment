from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
import math
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models import (
    Agent, AgentLocation, DeliveryAssignment, Order, User, Zone,
    AgentStatus, OrderStatus, UserRole
)
from app.services.order import OrderService
from app.services.notification import NotificationService
from app.schemas.agent import NearbyAgent
from app.db.session import get_db


class AgentService:
    """Service for agent management and assignment"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_service = OrderService(db)
    
    async def get_or_create_agent_profile(self, user_id: UUID) -> Agent:
        """Get or create agent profile for a user"""
        result = await self.db.execute(
            select(Agent).where(Agent.user_id == user_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            agent = Agent(
                id=uuid4(),
                user_id=user_id,
                employee_id=f"AGT{user_id.hex[:8].upper()}",
                status=AgentStatus.OFFLINE,
            )
            self.db.add(agent)
            await self.db.commit()
            await self.db.refresh(agent)
        return agent
    
    async def update_agent_status(self, agent_id: UUID, status: AgentStatus) -> Optional[Agent]:
        """Update agent availability status"""
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            return None
        
        agent.status = status
        await self.db.commit()
        await self.db.refresh(agent)
        return agent
    
    async def update_agent_location(
        self, 
        agent_id: UUID, 
        latitude: float, 
        longitude: float, 
        accuracy_meters: Optional[int] = None
    ) -> AgentLocation:
        """Update agent's current location"""
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found")
        
        # Find current zone based on location
        zone = await self._find_zone_by_coordinates(latitude, longitude)
        
        # Update or create location record
        result = await self.db.execute(
            select(AgentLocation).where(AgentLocation.agent_id == agent_id)
        )
        location = result.scalar_one_or_none()
        
        if location:
            location.latitude = Decimal(str(latitude))
            location.longitude = Decimal(str(longitude))
            location.accuracy_meters = accuracy_meters
            location.zone_id = zone.id if zone else None
            location.updated_at = datetime.utcnow()
        else:
            location = AgentLocation(
                id=uuid4(),
                agent_id=agent_id,
                latitude=Decimal(str(latitude)),
                longitude=Decimal(str(longitude)),
                accuracy_meters=accuracy_meters,
                zone_id=zone.id if zone else None,
            )
            self.db.add(location)
        
        # Update agent's zone if in a zone
        if zone and agent.zone_id != zone.id:
            agent.zone_id = zone.id
        
        await self.db.commit()
        await self.db.refresh(location)
        return location
    
    async def _find_zone_by_coordinates(self, latitude: float, longitude: float) -> Optional[Zone]:
        """Find zone containing the given coordinates (simplified - uses zone center proximity)"""
        # For MVP, we'll find the closest zone center
        # In production, you'd use PostGIS or proper geofencing
        result = await self.db.execute(
            select(Zone).where(Zone.is_active == True)
        )
        zones = result.scalars().all()
        
        # This is a placeholder - real implementation would use geospatial queries
        # For now, return None and rely on pincode-based zone detection
        return None
    
    def _calculate_distance(
        self, 
        lat1: float, lon1: float, 
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates in km (Haversine formula)"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def find_nearest_available_agents(
        self, 
        pickup_latitude: float, 
        pickup_longitude: float,
        max_distance_km: float = 50.0,
        limit: int = 10
    ) -> List[NearbyAgent]:
        """Find nearest available agents to pickup location"""
        # Get all available agents with locations
        result = await self.db.execute(
            select(Agent, AgentLocation, User)
            .join(AgentLocation, AgentLocation.agent_id == Agent.id, isouter=True)
            .join(User, User.id == Agent.user_id)
            .where(Agent.status == AgentStatus.AVAILABLE)
            .where(Agent.is_active == True)
            .where(User.is_active == True)
            .where(Agent.current_deliveries_count < Agent.max_concurrent_deliveries)
        )
        rows = result.all()
        
        nearby = []
        for agent, location, user in rows:
            if not location:
                continue
            
            distance = self._calculate_distance(
                pickup_latitude, pickup_longitude,
                float(location.latitude), float(location.longitude)
            )
            
            if distance <= max_distance_km:
                nearby.append(NearbyAgent(
                    agent_id=agent.id,
                    agent_name=user.full_name,
                    agent_phone=user.phone,
                    distance_km=round(distance, 2),
                    current_deliveries=agent.current_deliveries_count,
                    max_deliveries=agent.max_concurrent_deliveries,
                    status=agent.status
                ))
        
        # Sort by distance
        nearby.sort(key=lambda x: x.distance_km)
        return nearby[:limit]
    
    async def auto_assign_order(self, order_id: UUID) -> Optional[DeliveryAssignment]:
        """Auto-assign order to nearest available agent using zone→distance→load algorithm"""
        order = await self.order_service.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.CREATED:
            raise ValueError("Order must be in CREATED status for assignment")
        
        if order.agent_id:
            raise ValueError("Order already assigned")
        
        pickup_zone_id = order.pickup_zone_id
        if not pickup_zone_id:
            raise ValueError("Pickup zone not determined")
        
        # Get pickup zone for coordinates
        result = await self.db.execute(select(Zone).where(Zone.id == pickup_zone_id))
        pickup_zone = result.scalar_one_or_none()
        if not pickup_zone:
            raise ValueError("Pickup zone not found")
        
        # Use zone center coordinates
        if pickup_zone.latitude is None or pickup_zone.longitude is None:
            raise ValueError("Pickup zone center coordinates not configured")
        
        pickup_lat = float(pickup_zone.latitude)
        pickup_lon = float(pickup_zone.longitude)
        
        # First, try to find agents in the same zone
        result = await self.db.execute(
            select(Agent, AgentLocation, User)
            .join(User, User.id == Agent.user_id)
            .outerjoin(AgentLocation, AgentLocation.agent_id == Agent.id)
            .where(Agent.zone_id == pickup_zone_id)
            .where(Agent.status == AgentStatus.AVAILABLE)
            .where(Agent.is_active == True)
            .where(User.is_active == True)
            .where(Agent.current_deliveries_count < Agent.max_concurrent_deliveries)
        )
        same_zone_rows = result.all()
        
        candidates = []
        
        # Add same-zone agents with distance calculation
        for agent, location, user in same_zone_rows:
            if location:
                distance = self._calculate_distance(
                    pickup_lat, pickup_lon,
                    float(location.latitude), float(location.longitude)
                )
            else:
                # If no location, use a default large distance but still prefer same zone
                distance = 50.0
            
            candidates.append({
                'agent': agent,
                'user': user,
                'distance_km': distance,
                'zone_affinity': 0,  # Same zone = 0 (highest priority)
                'current_load': agent.current_deliveries_count,
                'max_load': agent.max_concurrent_deliveries,
            })
        
        # If no candidates in same zone, search nearby zones
        if not candidates:
            result = await self.db.execute(
                select(Agent, AgentLocation, User, Zone)
                .join(User, User.id == Agent.user_id)
                .outerjoin(AgentLocation, AgentLocation.agent_id == Agent.id)
                .join(Zone, Zone.id == Agent.zone_id)
                .where(Agent.zone_id != pickup_zone_id)
                .where(Agent.status == AgentStatus.AVAILABLE)
                .where(Agent.is_active == True)
                .where(User.is_active == True)
                .where(Agent.current_deliveries_count < Agent.max_concurrent_deliveries)
            )
            nearby_rows = result.all()
            
            for agent, location, user, zone in nearby_rows:
                if location:
                    distance = self._calculate_distance(
                        pickup_lat, pickup_lon,
                        float(location.latitude), float(location.longitude)
                    )
                else:
                    distance = 100.0
                
                candidates.append({
                    'agent': agent,
                    'user': user,
                    'distance_km': distance,
                    'zone_affinity': 1,  # Different zone = 1 (lower priority)
                    'current_load': agent.current_deliveries_count,
                    'max_load': agent.max_concurrent_deliveries,
                })
        
        if not candidates:
            return None
        
        # Sort by: zone_affinity (same zone first) -> distance -> current_load
        candidates.sort(key=lambda x: (x['zone_affinity'], x['distance_km'], x['current_load']))
        
        # Pick the best candidate
        best = candidates[0]
        agent = best['agent']
        user = best['user']
        
        # Check capacity before assignment
        if agent.current_deliveries_count >= agent.max_concurrent_deliveries:
            return None
        
        # Create assignment
        assignment = DeliveryAssignment(
            id=uuid4(),
            order_id=order_id,
            agent_id=agent.id,
            assigned_by=None,  # Auto-assigned
            is_auto_assigned=True,
        )
        self.db.add(assignment)
        
        # Update order and agent
        order.agent_id = agent.user_id
        order.status = OrderStatus.ASSIGNED
        agent.current_deliveries_count += 1
        agent.status = AgentStatus.BUSY
        
        # Create status history
        from app.models import OrderStatusHistory
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=OrderStatus.CREATED,
            new_status=OrderStatus.ASSIGNED,
            actor_id=agent.user_id,
            actor_role=UserRole.AGENT,
            reason=f"Auto-assigned to agent {user.full_name} (distance: {best['distance_km']:.1f}km)"
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(assignment)
        
        # Notify agent of new assignment
        notification_service = NotificationService(self.db)
        await notification_service.notify_agent_assignment(order_id, agent.id)
        
        return assignment
    
    async def manual_assign_order(
        self, 
        order_id: UUID, 
        agent_id: UUID, 
        admin_id: UUID
    ) -> Optional[DeliveryAssignment]:
        """Manually assign order to specific agent (admin only)"""
        order = await self.order_service.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.agent_id:
            raise ValueError("Order already assigned")
        
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found")
        
        if not agent.is_active:
            raise ValueError("Agent is not active")
        
        # Check capacity before assignment
        if agent.current_deliveries_count >= agent.max_concurrent_deliveries:
            raise ValueError("Agent has reached maximum concurrent deliveries")
        
        # Create assignment
        assignment = DeliveryAssignment(
            id=uuid4(),
            order_id=order_id,
            agent_id=agent_id,
            assigned_by=admin_id,
            is_auto_assigned=False,
        )
        self.db.add(assignment)
        
        # Update order and agent
        order.agent_id = agent.user_id
        order.status = OrderStatus.ASSIGNED
        agent.current_deliveries_count += 1
        agent.status = AgentStatus.BUSY
        
        # Create status history
        from app.models import OrderStatusHistory
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=OrderStatus.CREATED,
            new_status=OrderStatus.ASSIGNED,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
            reason=f"Manually assigned to agent"
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(assignment)
        
        # Notify agent of new assignment
        notification_service = NotificationService(self.db)
        await notification_service.notify_agent_assignment(order_id, agent_id)
        
        return assignment
    
    async def reassign_order(
        self, 
        order_id: UUID, 
        new_agent_id: UUID, 
        admin_id: UUID
    ) -> Optional[DeliveryAssignment]:
        """Reassign order to different agent"""
        order = await self.order_service.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if not order.agent_id:
            raise ValueError("Order not currently assigned")
        
        # Release current agent
        result = await self.db.execute(
            select(Agent).where(Agent.user_id == order.agent_id)
        )
        old_agent = result.scalar_one_or_none()
        if old_agent:
            old_agent.current_deliveries_count = max(0, old_agent.current_deliveries_count - 1)
            if old_agent.current_deliveries_count == 0:
                old_agent.status = AgentStatus.AVAILABLE
        
        # Assign to new agent
        result = await self.db.execute(select(Agent).where(Agent.id == new_agent_id))
        new_agent = result.scalar_one_or_none()
        if not new_agent:
            raise ValueError("New agent not found")
        
        # Update assignment
        result = await self.db.execute(
            select(DeliveryAssignment).where(DeliveryAssignment.order_id == order_id)
        )
        assignment = result.scalar_one_or_none()
        if assignment:
            assignment.agent_id = new_agent_id
            assignment.assigned_by = admin_id
            assignment.is_auto_assigned = False
            assignment.accepted_at = None
        
        # Update order and new agent
        order.agent_id = new_agent.user_id
        new_agent.current_deliveries_count += 1
        new_agent.status = AgentStatus.BUSY
        
        # Create status history
        from app.models import OrderStatusHistory
        history = OrderStatusHistory(
            id=uuid4(),
            order_id=order.id,
            old_status=order.status,
            new_status=order.status,
            actor_id=admin_id,
            actor_role=UserRole.ADMIN,
            reason=f"Reassigned to new agent"
        )
        self.db.add(history)
        
        await self.db.commit()
        return assignment
    
    async def complete_delivery(self, order_id: UUID, agent_id: UUID) -> bool:
        """Mark delivery as completed and release agent"""
        order = await self.order_service.get_order(order_id)
        if not order:
            return False
        
        if order.agent_id != agent_id:
            raise ValueError("Not assigned to this agent")
        
        # Update order status
        await self.order_service.update_order_status(
            order_id=order_id,
            new_status=OrderStatus.DELIVERED,
            actor_id=agent_id,
            actor_role=UserRole.AGENT,
            reason="Delivery completed"
        )
        
        # Release agent
        result = await self.db.execute(
            select(Agent).where(Agent.user_id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if agent:
            agent.current_deliveries_count = max(0, agent.current_deliveries_count - 1)
            if agent.current_deliveries_count == 0:
                agent.status = AgentStatus.AVAILABLE
        
        await self.db.commit()
        return True
    
    async def get_agent_dashboard(self, agent_id: UUID) -> dict:
        """Get agent dashboard data"""
        result = await self.db.execute(
            select(Agent)
            .options(selectinload(Agent.user))
            .where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            return None
        
        # Get assigned orders
        result = await self.db.execute(
            select(Order)
            .where(Order.agent_id == agent.user_id)
            .where(Order.status.in_([OrderStatus.PICKED_UP, OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY]))
            .order_by(Order.created_at.desc())
        )
        active_orders = result.scalars().all()
        
        # Get recent completed orders
        result = await self.db.execute(
            select(Order)
            .where(Order.agent_id == agent.user_id)
            .where(Order.status == OrderStatus.DELIVERED)
            .order_by(Order.delivered_at.desc())
            .limit(10)
        )
        recent_orders = result.scalars().all()
        
        return {
            "agent": agent,
            "active_orders": active_orders,
            "recent_orders": recent_orders,
            "stats": {
                "current_deliveries": agent.current_deliveries_count,
                "max_deliveries": agent.max_concurrent_deliveries,
                "status": agent.status,
            }
        }


async def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    from fastapi import Depends
    from app.db.session import get_db
    return AgentService(db)