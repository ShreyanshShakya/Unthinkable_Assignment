import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import unique_email


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_customer(client):
    email = unique_email("customer")
    response = await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Test User",
        "password": "pwd12345",
        "role": "customer"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Test User"
    assert data["role"] == "customer"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    email = unique_email("dup")
    await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "User 1",
        "password": "pwd12345",
        "role": "customer"
    })
    response = await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "User 2",
        "password": "pwd12345",
        "role": "customer"
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    email = unique_email("login")
    await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Login User",
        "password": "pwd12345",
        "role": "customer"
    })
    response = await client.post("/api/auth/login", json={
        "email": email,
        "password": "pwd123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    email = unique_email("wrongpass")
    await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Wrong Pass",
        "password": "pwd12345",
        "role": "customer"
    })
    response = await client.post("/api/auth/login", json={
        "email": email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/api/auth/login", json={
        "email": unique_email("nonexistent"),
        "password": "pwd12345"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    email = unique_email("refresh")
    await client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Refresh User",
        "password": "pwd12345",
        "role": "customer"
    })
    login_resp = await client.post("/api/auth/login", json={
        "email": email,
        "password": "pwd123"
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
