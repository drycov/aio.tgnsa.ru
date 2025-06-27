from typing import AsyncGenerator, Callable, Any
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

__all__ = (
    "engine",
    "SessionLocal",
    "get_session",
    "session_from_generator",
    "get_sessionmaker",
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Создание движка и фабрики асинхронных сессий
# ─────────────────────────────────────────────────────────────────────────────
engine = create_async_engine(settings.db.get_dsn(), echo=False, future=True)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Депенденси для FastAPI
# ─────────────────────────────────────────────────────────────────────────────
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронное создание сессии для FastAPI.

    Используется как Depends(get_session).
    При завершении запроса сессия автоматически закрывается.
    """
    async with SessionLocal() as session:
        yield session


# ─────────────────────────────────────────────────────────────────────────────
# 3. Контекстный менеджер для aiogram
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def session_from_generator(
    session_gen: Callable[..., AsyncGenerator[AsyncSession, Any]],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Позволяет вручную получить сессию из генератора (например, get_session) вне FastAPI.

    Пример:
        async with session_from_generator(get_session) as session:
            result = await session.execute(...)
            ...

    Сессия закрывается автоматически.
    """
    session = await session_gen().__anext__()
    try:
        yield session
    finally:
        await session.close()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Прямая фабрика сессий
# ─────────────────────────────────────────────────────────────────────────────
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Возвращает объект async_sessionmaker для создания сессий вручную.
    Например:
        session = get_sessionmaker()()
        await session.begin()
        ...
    """
    return SessionLocal
