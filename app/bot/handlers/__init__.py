from aiogram import Dispatcher
from pydantic_settings import BaseSettings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.utils.logger_manager import LoggerManager

from .startHandler import router as start_router

def register_handlers(
    dp: Dispatcher,
    *,
    db_sessionmaker: async_sessionmaker,
    settings: BaseSettings,
    logger: LoggerManager,
    redis: Redis | None = None,
):
    """
    Регистрирует все роутеры и связанные обработчики.
    """

    # Подключаем routers (маршрутизаторы по областям)
    dp.include_router(start_router)

    logger.debug("✅ Роутеры зарегистрированы")

    # [Опционально] Проброс глобальных данных — если это не middleware
    dp.workflow_data.update({
        "db": db_sessionmaker,
        "settings": settings,
        "logger": logger,
        "redis": redis,
    })
    logger.debug("🔧 workflow_data обновлена")
