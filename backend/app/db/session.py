from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()


def create_engine(database_url: str | None = None):
    url = database_url or settings.DATABASE_URL
    if settings.ENVIRONMENT == "test" or database_url:
        return create_async_engine(
            url,
            poolclass=NullPool,
            echo=settings.DEBUG,
        )
    return create_async_engine(
        url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )


def create_session_factory(database_url: str | None = None):
    engine = create_engine(database_url)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


AsyncSessionLocal = create_session_factory()
engine = create_engine()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(database_url: str | None = None) -> None:
    eng = create_engine(database_url)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)