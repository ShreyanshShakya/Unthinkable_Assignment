import os
import uuid

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_lastmile"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars-long"

import asyncio


def unique_email(prefix: str = "user") -> str:
    """Generate a unique email for test isolation."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from app.db.base import Base
from app.db.session import get_db, init_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for testing"""
    with PostgresContainer("postgres:15") as postgres:
        url = postgres.get_connection_url()
        # Replace psycopg2 driver with asyncpg for async engine
        if url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        yield url


@pytest.fixture(scope="session")
async def test_engine(postgres_container):
    eng = create_async_engine(postgres_container, poolclass=NullPool, echo=False)

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture(autouse=True, scope="session")
async def override_lifespan(test_engine):
    """Override the lifespan to use test database"""
    original_init_db = init_db

    async def test_init_db(database_url=None):
        pass  # Tables already created by test_engine fixture

    import app.db.session
    app.db.session.init_db = test_init_db

    # Also override the engine in session module
    from app.db import session as session_module
    session_module.engine = test_engine
    session_module.AsyncSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    yield

    # Restore
    app.db.session.init_db = original_init_db


@pytest.fixture
async def test_db(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_engine):
    test_session_local = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with test_session_local() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(test_engine):
    """Authenticated client with a registered customer (short password)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register a user with short password (<=72 bytes, min 8 chars)
        email = unique_email("customer")
        await ac.post("/api/auth/register", json={
            "email": email,
            "full_name": "Test Customer",
            "password": "pwd12345",
            "role": "customer"
        })
        # Login to obtain tokens
        login_resp = await ac.post("/api/auth/login", json={
            "email": email,
            "password": "pwd12345"
        })
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        ac.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
        yield ac
