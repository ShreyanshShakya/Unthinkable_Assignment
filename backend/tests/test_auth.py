import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import UserRole


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_customer(client):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123",
        "role": "customer"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "customer"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "full_name": "User 1",
        "password": "password123",
        "role": "customer"
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "full_name": "User 2",
        "password": "password123",
        "role": "customer"
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "full_name": "Login User",
        "password": "password123",
        "role": "customer"
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "wrongpass@example.com",
        "full_name": "Wrong Pass",
        "password": "password123",
        "role": "customer"
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/api/auth/register", json={
        "email": "refresh@example.com",
        "full_name": "Refresh User",
        "password": "password123",
        "role": "customer"
    })
    login_resp = await client.post("/api/auth/login", json={
        "email": "refresh@example.com",
        "password": "password123"
    })
    refresh_token = login_resp.json()["refresh_token"]
    
    response = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_invalid_refresh_token(client):
    response = await client.post("/api/auth/refresh", json={
        "refresh_token": "invalid.token.here"
    })
    assert response.status_code == 401