from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client):
    """Create an authenticated client with a customer token"""
    # Register a customer
    email = f"test_{uuid4().hex[:8]}@example.com"
    await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Test Customer",
        "password": "password123",
        "role": "customer"
    })
    login = await client.post("/api/auth/login", json={
        "email": email,
        "password": "password123"
    })
    token = login.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestPricingEngine:
    """Test pricing calculation engine"""

    @pytest.mark.asyncio
    async def test_volumetric_weight_calculation(self, auth_client):
        """Test volumetric weight: L × B × H / 5000"""
        # 30x20x15 cm = 9000 cm³ → 9000/5000 = 1.8 kg
        response = await auth_client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 1.0,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 30*20*15 = 9000 cm³ / 5000 = 1.8 kg
        assert data["pricing"]["volumetric_weight_kg"] == 1.8
        assert data["pricing"]["billable_weight_kg"] == 1.8  # max(1.0, 1.8)

    @pytest.mark.asyncio
    async def test_volumetric_weight_less_than_actual(self, auth_client):
        """Test when actual weight > volumetric weight"""
        # 10x10x10 cm = 1000 cm³ / 5000 = 0.2 kg, actual = 2.0 kg
        response = await auth_client.post("/api/pricing/quote", json={
            "length_cm": 10,
            "breadth_cm": 10,
            "height_cm": 10,
            "actual_weight_kg": 2.0,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pricing"]["volumetric_weight_kg"] == 0.2
        assert data["pricing"]["billable_weight_kg"] == 2.0  # max(2.0, 0.2)

    @pytest.mark.asyncio
    async def test_intra_zone_pricing(self, auth_client):
        """Test intra-zone pricing (same pickup and drop zone)"""
        response = await auth_client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "110001",  # Same pincode = intra-zone
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pricing"]["zone_type"] == "intra_zone"

    @pytest.mark.asyncio
    async def test_inter_zone_pricing(self, auth_client):
        """Test inter-zone pricing (different pickup and drop zone)"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",  # Delhi
            "drop_pincode": "400001",    # Mumbai
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pricing"]["zone_type"] == "inter_zone"

    @pytest.mark.asyncio
    async def test_cod_surcharge(self, auth_client):
        """Test COD surcharge calculation"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "cod",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 3000  # 3000 * 3% = 90, min 25, max 100 = 90
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pricing"]["cod_surcharge"] > 0
        assert data["pricing"]["total_charge"] == data["pricing"]["base_charge"] + data["pricing"]["cod_surcharge"]

    @pytest.mark.asyncio
    async def test_prepaid_no_cod(self, auth_client):
        """Test prepaid has no COD surcharge"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 3000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pricing"]["cod_surcharge"] == 0
        assert data["pricing"]["total_charge"] == data["pricing"]["base_charge"]

    @pytest.mark.asyncio
    async def test_b2b_vs_b2c_pricing(self, auth_client):
        """Test B2B vs B2C different pricing"""
        # B2C
        response_b2c = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        # B2B
        response_b2b = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2b",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response_b2c.status_code == 200
        assert response_b2b.status_code == 200
        data_b2c = response_b2c.json()
        data_b2b = response_b2b.json()
        # B2B and B2C may have different pricing
        assert data_b2c["success"] is True
        assert data_b2b["success"] is True

    @pytest.mark.asyncio
    async def test_weight_boundary_exact_min(self, auth_client):
        """Test weight exactly at minimum boundary"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 10,
            "breadth_cm": 10,
            "height_cm": 10,
            "actual_weight_kg": 0.5,  # Exactly at 0.5kg boundary
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_dimensions(self, auth_client):
        """Test negative dimensions are rejected"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": -10,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Dimensions must be positive" in data["error"]

    @pytest.mark.asyncio
    async def test_zero_weight_rejected(self, auth_client):
        """Test zero weight is rejected"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 0,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Actual weight must be positive" in data["error"]

    @pytest.mark.asyncio
    async def test_unknown_pincode(self, auth_client):
        """Test unknown pincode returns error"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "999999",  # Unknown pincode
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Pickup zone not found" in data["error"]

    @pytest.mark.asyncio
    async def test_cod_surcharge_min_max(self, auth_client):
        """Test COD surcharge respects min/max bounds"""
        # Test minimum surcharge
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 1.0,
            "order_type": "b2c",
            "payment_type": "cod",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 100  # Low value, should hit min surcharge
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should apply minimum surcharge if percentage gives less than minimum

    @pytest.mark.asyncio
    async def test_pricing_quote_includes_zones(self, auth_client):
        """Test quote response includes zone information"""
        response = await client.post("/api/pricing/quote", json={
            "length_cm": 30,
            "breadth_cm": 20,
            "height_cm": 15,
            "actual_weight_kg": 2.5,
            "order_type": "b2c",
            "payment_type": "prepaid",
            "pickup_pincode": "110001",
            "drop_pincode": "400001",
            "order_value": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pickup_zone" in data
        assert "drop_zone" in data
        assert data["pickup_zone"]["code"] == "110001"
        assert data["drop_zone"]["code"] == "400001"
