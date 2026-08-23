import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import OrderType, PaymentType, ZoneType
from uuid import uuid4
from decimal import Decimal


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()