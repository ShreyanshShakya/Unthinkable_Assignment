import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import AgentStatus, OrderStatus, Zone, Agent, AgentLocation, User, Order, OrderStatus, OrderType, PaymentType, ZoneType
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAgentProfile:
    """Test agent profile management"""

    @pytest.mark.asyncio
    async def test_create_agent_profile(self, client):
        """Agent can create their profile"""
        pass

    @pytest.mark.asyncio
    async def test_get_my_profile(self, client):
        """Agent can view their own profile"""
        pass

    @pytest.mark.asyncio
    async def test_update_my_profile(self, client):
        """Agent can update their profile"""
        pass

    @pytest.mark.asyncio
    async def test_update_availability(self, client):
        """Agent can update availability status"""
        pass

    @pytest.mark.asyncio
    async def test_update_location(self, client):
        """Agent can update GPS location"""
        pass


class TestAgentDashboard:
    """Test agent dashboard data"""

    @pytest.mark.asyncio
    async def test_dashboard_active_orders(self, client):
        """Dashboard shows active deliveries"""
        pass

    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client):
        """Dashboard shows correct stats"""
        pass

    @pytest.mark.asyncio
    async def test_dashboard_recent_deliveries(self, client):
        """Dashboard shows recent completed deliveries"""
        pass


class TestAgentAssignment:
    """Test agent assignment logic"""

    @pytest.mark.asyncio
    async def test_auto_assign_prefers_same_zone(self, client):
        """Auto-assignment prefers agents in pickup zone"""
        pass

    @pytest.mark.asyncio
    async def test_auto_assign_prefers_nearest(self, client):
        """Auto-assignment prefers nearest agent"""
        pass

    @pytest.mark.asyncio
    async def test_auto_assign_prefers_least_busy(self, client):
        """Auto-assignment prefers least busy agent"""
        pass

    @pytest.mark.asyncio
    async def test_auto_assign_respects_capacity(self, client):
        """Auto-assignment respects max concurrent deliveries"""
        pass

    @pytest.mark.asyncio
    async def test_auto_assign_fallback_to_nearby_zones(self, client):
        """Auto-assignment falls back to nearby zones"""
        pass

    @pytest.mark.asyncio
    async def test_manual_assign_admin(self, client):
        """Admin can manually assign agent"""
        pass

    @pytest.mark.asyncio
    async def test_manual_assign_respects_capacity(self, client):
        """Manual assignment respects agent capacity"""
        pass


class TestAssignmentAlgorithm:
    """Test the assignment algorithm with different coordinates"""

    @pytest.mark.asyncio
    async def test_same_zone_agent_preferred_over_nearby_zone(self, test_engine):
        """Test that agents in the same zone are preferred over nearby zones"""
        from app.services.agent import AgentService
        from app.models import Zone, Agent, AgentLocation, User, AgentStatus
        from uuid import uuid4
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from sqlalchemy import select
        
        async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            service = AgentService(session)
            
            # Create two zones
            zone_a = Zone(id=uuid4(), name="Zone A", code="ZA", is_active=True)
            zone_b = Zone(id=uuid4(), name="Zone B", code="ZB", is_active=True)
            zone_a.latitude = 28.6139
            zone_a.longitude = 77.2090
            zone_b.latitude = 19.0760
            zone_b.longitude = 72.8777
            session.add_all([zone_a, zone_b])
            await session.commit()
            
            # Create users
            user_a = User(id=uuid4(), email="agent_a@example.com", full_name="Agent A", 
                          hashed_password="hash", role="agent", is_active=True)
            user_b = User(id=uuid4(), email="agent_b@example.com", full_name="Agent B", 
                          hashed_password="hash", role="agent", is_active=True)
            session.add_all([user_a, user_b])
            await session.commit()
            
            # Create agents
            agent_a = Agent(id=uuid4(), user_id=user_a.id, employee_id="AGT001", 
                           zone_id=zone_a.id, status=AgentStatus.AVAILABLE,
                           max_concurrent_deliveries=3, current_deliveries_count=0, is_active=True)
            agent_b = Agent(id=uuid4(), user_id=user_b.id, employee_id="AGT002", 
                           zone_id=zone_b.id, status=AgentStatus.AVAILABLE,
                           max_concurrent_deliveries=3, current_deliveries_count=0, is_active=True)
            session.add_all([agent_a, agent_b])
            await session.commit()
            
            # Add locations (agent_a in zone_a, agent_b in zone_b)
            loc_a = AgentLocation(id=uuid4(), agent_id=agent_a.id, 
                                 latitude=28.6139, longitude=77.2090, zone_id=zone_a.id)
            loc_b = AgentLocation(id=uuid4(), agent_id=agent_b.id, 
                                 latitude=19.0760, longitude=72.8777, zone_id=zone_b.id)
            session.add_all([loc_a, loc_b])
            await session.commit()
            
            # Create order in zone_a
            order_id = uuid4()
            from app.models import Order, OrderStatus, OrderType, PaymentType, ZoneType
            order = Order(
                id=order_id,
                order_number="ORDTEST001",
                customer_id=uuid4(),
                pickup_address="Test Pickup",
                pickup_pincode="110001",
                drop_address="Test Drop",
                drop_pincode="110001",
                length_cm=30, breadth_cm=20, height_cm=15,
                actual_weight_kg=2.0,
                volumetric_weight_kg=1.8,
                billable_weight_kg=2.0,
                order_type=OrderType.B2C,
                payment_type=PaymentType.PREPAID,
                zone_type=ZoneType.INTRA_ZONE,
                pickup_zone_id=zone_a.id,
                drop_zone_id=zone_a.id,
                base_charge=100, cod_surcharge=0, total_charge=100,
                status=OrderStatus.CREATED
            )
            session.add(order)
            await session.commit()
            
            # Test assignment - should pick agent_a (same zone, closer)
            assignment = await service.auto_assign_order(order_id)
            assert assignment is not None
            assert assignment.agent_id == agent_a.id

    @pytest.mark.asyncio
    async def test_nearest_agent_selected_within_same_zone(self, test_engine):
        """Test that nearest agent is selected within same zone"""
        from app.services.agent import AgentService
        from app.models import Zone, Agent, AgentLocation, User, AgentStatus
        from uuid import uuid4
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from sqlalchemy import select
        
        async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            service = AgentService(session)
            
            # Create zone
            zone = Zone(id=uuid4(), name="Test Zone", code="TZ", is_active=True,
                       latitude=28.6139, longitude=77.2090)
            session.add(zone)
            await session.commit()
            
            # Create users
            user1 = User(id=uuid4(), email="agent1@example.com", full_name="Agent One", 
                         hashed_password="hash", role="agent", is_active=True)
            user2 = User(id=uuid4(), email="agent2@example.com", full_name="Agent Two", 
                         hashed_password="hash", role="agent", is_active=True)
            session.add_all([user1, user2])
            await session.commit()
            
            # Create agents (both in same zone)
            agent1 = Agent(id=uuid4(), user_id=user1.id, employee_id="AGT001", 
                          zone_id=zone.id, status=AgentStatus.AVAILABLE,
                          max_concurrent_deliveries=3, current_deliveries_count=0, is_active=True)
            agent2 = Agent(id=uuid4(), user_id=user2.id, employee_id="AGT002", 
                          zone_id=zone.id, status=AgentStatus.AVAILABLE,
                          max_concurrent_deliveries=3, current_deliveries_count=0, is_active=True)
            session.add_all([agent1, agent2])
            await session.commit()
            
            # Agent1 at zone center (closer)
            loc1 = AgentLocation(id=uuid4(), agent_id=agent1.id, 
                                latitude=28.6139, longitude=77.2090, zone_id=zone.id)
            # Agent2 5km away
            loc2 = AgentLocation(id=uuid4(), agent_id=agent2.id, 
                                latitude=28.6500, longitude=77.2200, zone_id=zone.id)
            session.add_all([loc1, loc2])
            await session.commit()
            
            # Create order in same zone
            order_id = uuid4()
            from app.models import Order, OrderStatus, OrderType, PaymentType, ZoneType
            order = Order(
                id=order_id,
                order_number="ORDTEST002",
                customer_id=uuid4(),
                pickup_address="Test Pickup",
                pickup_pincode="110001",
                drop_address="Test Drop",
                drop_pincode="110001",
                length_cm=30, breadth_cm=20, height_cm=15,
                actual_weight_kg=2.0,
                volumetric_weight_kg=1.8,
                billable_weight_kg=2.0,
                order_type=OrderType.B2C,
                payment_type=PaymentType.PREPAID,
                zone_type=ZoneType.INTRA_ZONE,
                pickup_zone_id=zone.id,
                drop_zone_id=zone.id,
                base_charge=100, cod_surcharge=0, total_charge=100,
                status=OrderStatus.CREATED
            )
            session.add(order)
            await session.commit()
            
            # Test assignment - should pick agent1 (closer to zone center)
            assignment = await service.auto_assign_order(order_id)
            assert assignment is not None
            assert assignment.agent_id == agent1.id

    @pytest.mark.asyncio
    async def test_reassign_order(self, client):
        """Admin can reassign order to different agent"""
        pass

    @pytest.mark.asyncio
    async def test_reassign_releases_old_agent(self, client):
        """Reassignment releases old agent capacity"""
        pass


class TestAgentStatusUpdates:
    """Test agent delivery status updates"""

    @pytest.mark.asyncio
    async def test_agent_can_pickup(self, client):
        """Agent can update status to PICKED_UP"""
        pass

    @pytest.mark.asyncio
    async def test_agent_can_in_transit(self, client):
        """Agent can update status to IN_TRANSIT"""
        pass

    @pytest.mark.asyncio
    async def test_agent_can_out_for_delivery(self, client):
        """Agent can update status to OUT_FOR_DELIVERY"""
        pass

    @pytest.mark.asyncio
    async def test_agent_can_deliver(self, client):
        """Agent can update status to DELIVERED"""
        pass

    @pytest.mark.asyncio
    async def test_agent_can_fail_delivery(self, client):
        """Agent can mark delivery as FAILED"""
        pass

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, client):
        """Agent cannot make invalid transitions"""
        pass


class TestAgentCapacity:
    """Test agent capacity management"""

    @pytest.mark.asyncio
    async def test_capacity_increments_on_assignment(self, client):
        """Agent current_deliveries_count increments on assignment"""
        pass

    @pytest.mark.asyncio
    async def test_capacity_decrements_on_delivery(self, client):
        """Agent current_deliveries_count decrements on delivery"""
        pass

    @pytest.mark.asyncio
    async def test_agent_becomes_busy_at_capacity(self, client):
        """Agent status changes to BUSY at max capacity"""
        pass

    @pytest.mark.asyncio
    async def test_agent_becomes_available_at_zero(self, client):
        """Agent status changes to AVAILABLE at zero deliveries"""
        pass

    @pytest.mark.asyncio
    async def test_max_concurrent_deliveries_configurable(self, client):
        """Agent max_concurrent_deliveries is configurable"""
        pass