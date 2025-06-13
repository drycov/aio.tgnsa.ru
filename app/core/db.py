from typing import AsyncGenerator, Callable, Any
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.base import Base
from app.core.config import settings

__all__ = ("engine", "SessionLocal", "get_session")

# Создание асинхронного движка и фабрики сессий
engine = create_async_engine(settings.db.get_dsn(), echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор SQLAlchemy-сессии.
    Используется в FastAPI как Depends(get_session).
    """
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def session_from_generator(
    session_gen: Callable[..., AsyncGenerator[AsyncSession, Any]]
) -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для извлечения сессии из генератора вручную (например, в aiogram).
    Обеспечивает безопасное закрытие после использования.
    """
    session = await session_gen.__anext__()
    try:
        yield session
    finally:
        await session.close()
