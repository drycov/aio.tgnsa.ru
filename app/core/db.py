from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.base import Base
from app.core.config import settings

__all__ = ("engine", "SessionLocal", "get_session")

engine = create_async_engine(settings.db.get_dsn(), echo=settings.db.echo)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
