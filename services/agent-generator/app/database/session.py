"""
Database session management for Agent Generator Service.

Provides async database session handling for SQLAlchemy.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.database import Base

# =============================================================================
# Async Engine
# =============================================================================

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
    future=True,
)

# =============================================================================
# Session Factory
# =============================================================================

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# Dependency
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields a session and ensures cleanup after use.

    Usage in FastAPI:
        @router.get("/agents")
        async def list_agents(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# =============================================================================
# Initialization
# =============================================================================

async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables if they don't exist.

    NOTE: For production, use Alembic migrations instead:
        cd services/agent-generator
        alembic upgrade head

    This init_db() is kept for development/testing convenience.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
