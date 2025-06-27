from aiogram import Dispatcher
from pydantic_settings import BaseSettings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.utils.logger_manager import LoggerManager

from .main_handlers.main_commands import router as main_router
from .register_handlers.registration_handler import router as registration_router
from .admin_handlers.admin_callback import router as admin_callback
from .startHandler import router as start_router
from .error_handler import router as error_router

from app.bot.middlewares.database import DatabaseMiddleware


def register_handlers(
    dp: Dispatcher,
    *,
    db_sessionmaker: async_sessionmaker,
    settings: BaseSettings,
    logger: LoggerManager,
    redis: Redis | None = None,
):
    """
    Регистрирует все роутеры и middleware.
    """
    # Проброс глобальных данных
    dp.workflow_data.update(
        {
            "db": db_sessionmaker,
            "settings": settings,
            "logger": logger,
            "redis": redis,
        }
    )
    logger.debug("🔧 workflow_data обновлена")

    # Регистрация middleware
    dp.message.middleware(
        DatabaseMiddleware(sessionmaker=db_sessionmaker, logger=logger)
    )
    dp.callback_query.middleware(
        DatabaseMiddleware(sessionmaker=db_sessionmaker, logger=logger)
    )
    logger.debug("🧩 DatabaseMiddleware подключён")

    # Подключение feature-based маршрутов
    dp.include_router(error_router)
    dp.include_router(start_router)
    dp.include_router(main_router)
    dp.include_router(registration_router)
    dp.include_router(admin_callback)

    logger.debug("✅ Роутеры зарегистрированы")
