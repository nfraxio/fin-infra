"""Database setup and exports for fin-infra-template."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fin_infra_template.db.base import Base
from fin_infra_template.settings import settings

__all__ = ["Base", "get_engine", "get_session"]

# Global engine instance
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.sql_url,
            pool_size=settings.sql_pool_size,
            max_overflow=settings.sql_max_overflow,
            pool_timeout=settings.sql_pool_timeout,
            echo=False,
        )
    return _engine


async def get_session() -> AsyncSession:
    """Get an async database session."""
    engine = get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
