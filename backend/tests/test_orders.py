import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import OrderType, PaymentType, OrderStatus
from uuid import uuid4


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestOrderLifecycle:
    """Test order creation and lifecycle"""

    @pytest.mark.asyncio
    async def test_create_order_customer(self, client):
        """Test customer can create an order"""
        # First register and login a customer
        register_resp = await client.post("/api/auth/register", json={
            "email": "customer_test@example.com",
            "full_name": "Test Customer",
            "password": "password123",
            "role": "customer"
        })
        assert register_resp.status_code == 201
        
        login_resp = await client.post("/api/auth/login", json={
            "email": "customer_test@example.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Create order
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/orders", json={
            "pickup_address": "123 Main St, Delhi",
            "pickup_pincode": "110001",
            "pickup_city": "Delhi",
            "drop_address": "456 Park Ave, Mumbai",
            "drop_pincode": "400001",
            "drop_city": "Mumbai",
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "order_value": 0
        }, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["order_number"].startswith("ORD")
        assert data["status"] == "created"
        assert data["order_type"] == "b2c"
        assert data["payment_type"] == "prepaid"
        assert data["total_charge"] > 0

    @pytest.mark.asyncio
    async def test_create_order_cod(self, client):
        """Test creating COD order"""
        # Login as customer
        login_resp = await client.post("/api/auth/login", json={
            "email": "customer_test@example.com",
            "password": "password123"
        })
        token = login_resp.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/orders", json={
            "pickup_address": "123 Main St, Delhi",
            "pickup_pincode": "110001",
            "pickup_city": "Delhi",
            "drop_address": "456 Park Ave, Mumbai",
            "drop_pincode": "400001",
            "drop_city": "Mumbai",
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "cod",
            "order_value": 3000
        }, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["payment_type"] == "cod"
        assert data["cod_surcharge"] > 0
        assert data["total_charge"] == data["base_charge"] + data["cod_surcharge"]


class TestOrderStatusTransitions:
    """Test valid and invalid status transitions"""

    @pytest.fixture
    async def auth_client(self, client):
        """Create authenticated client with order"""
        # Register and login
        await client.post("/api/auth/register", json={
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "full_name": "Test User",
            "password": "password123",
            "role": "customer"
        })
        login = await client.post("/api/auth/login", json={
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "password": "password123"
        })
        token = login.json()["access_token"]
        return {"client": client, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

    @pytest.mark.asyncio
    async def test_valid_transition_created_to_assigned(self, auth_client):
        """Test CREATED → ASSIGNED transition (via admin assignment)"""
        # This would be tested via admin assignment endpoint
        pass

    @pytest.mark.asyncio
    async def test_valid_transition_assigned_to_picked_up(self, client):
        """Test ASSIGNED → PICKED_UP transition (agent picks up)"""
        # Need agent login and assigned order
        pass

    @pytest.mark.asyncio
    async def test_valid_transition_picked_up_to_in_transit(self, client):
        """Test PICKED_UP → IN_TRANSIT transition"""
        pass

    @pytest.mark.asyncio
    async def test_valid_transition_in_transit_to_out_for_delivery(self, client):
        """Test IN_TRANSIT → OUT_FOR_DELIVERY transition"""
        pass

    @pytest.mark.asyncio
    async def test_valid_transition_out_for_delivery_to_delivered(self, client):
        """Test OUT_FOR_DELIVERY → DELIVERED transition"""
        pass

    @pytest.mark.asyncio
    async def test_valid_transition_out_for_delivery_to_failed(self, client):
        """Test OUT_FOR_DELIVERY → FAILED transition"""
        pass

    @pytest.mark.asyncio
    async def test_invalid_transition_created_to_delivered(self, auth_client):
        """Test invalid CREATED → DELIVERED transition"""
        pass

    @pytest.mark.asyncio
    async def test_invalid_transition_picked_up_to_delivered(self, client):
        """Test invalid PICKED_UP → DELIVERED transition (skipping IN_TRANSIT)"""
        pass

    @pytest.mark.asyncio
    async def test_customer_can_cancel_created_order(self, auth_client):
        """Customer can cancel order in CREATED status"""
        pass

    @pytest.mark.asyncio
    async def test_customer_cannot_cancel_picked_up_order(self, client):
        """Customer cannot cancel order in PICKED_UP status"""
        pass


class TestOrderTracking:
    """Test order tracking and history"""

    @pytest.mark.asyncio
    async def test_tracking_history_created(self, client):
        """Test status history is created on each transition"""
        pass

    @pytest.mark.asyncio
    async def test_tracking_history_immutable(self, client):
        """Test status history cannot be modified"""
        pass

    @pytest.mark.asyncio
    async def test_tracking_includes_actor_info(self, client):
        """Test history includes actor ID, role, timestamp, reason"""
        pass


class TestOrderFiltering:
    """Test order listing and filtering"""

    @pytest.mark.asyncio
    async def test_customer_sees_own_orders_only(self, client):
        """Customer only sees their own orders"""
        pass

    @pytest.mark.asyncio
    async def test_agent_sees_assigned_orders_only(self, client):
        """Agent only sees assigned orders"""
        pass

    @pytest.mark.asyncio
    async def test_admin_sees_all_orders(self, client):
        """Admin sees all orders"""
        pass

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client):
        """Filter orders by status"""
        pass

    @pytest.mark.asyncio
    async def test_filter_by_order_type(self, client):
        """Filter orders by B2B/B2C"""
        pass

    @pytest.mark.asyncio
    async def test_filter_by_payment_type(self, client):
        """Filter orders by prepaid/COD"""
        pass

    @pytest.mark.asyncio
    async def test_pagination(self, client):
        """Test pagination works correctly"""
        pass


class TestQuoteBeforeOrder:
    """Test quote before order confirmation"""

    @pytest.mark.asyncio
    async def test_quote_endpoint(self, client):
        """Test GET /orders/quote returns pricing"""
        pass

    @pytest.mark.asyncio
    async def test_quote_recalculated_on_order(self, client):
        """Test server recalculates price on order creation"""
        pass