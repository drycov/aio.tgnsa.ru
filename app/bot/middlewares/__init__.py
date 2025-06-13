from typing import Any

from aiogram import Dispatcher
from pydantic_settings import BaseSettings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.utils.logger_manager import LoggerManager

from .auth import AuthMiddleware
from .banned import BannedCheckMiddleware
from .command_log import CommandLoggingMiddleware
from .profiler import ProfilerMiddleware
from .role import RoleMiddleware
from .tfa import TfaMiddleware


class InjectMiddleware:
    def __init__(self, key: str, value: Any, logger: LoggerManager | None = None):
        self.key = key
        self.value = value
        self.logger = logger

    async def __call__(self, handler, event, data):
        data[self.key] = self.value
        if self.logger:
            self.logger.debug(f"📦 Значение '{self.key}' внедрено в data.")
        return await handler(event, data)


def register_middlewares(
    dp: Dispatcher,
    *,
    db_sessionmaker: async_sessionmaker,
    settings: BaseSettings,
    logger: LoggerManager,
    redis: Redis | None = None,
):
    """Регистрирует все middleware в нужном порядке."""

    logger.debug("🔧 Регистрация middleware...")

    # Технические middleware
    dp.message.middleware(ProfilerMiddleware(logger=logger))
    logger.debug("✅ ProfilerMiddleware зарегистрирован.")

    dp.message.middleware(CommandLoggingMiddleware(logger=logger))
    logger.debug("✅ CommandLoggingMiddleware зарегистрирован.")

    # Бизнес-логика
    dp.message.middleware(AuthMiddleware(logger=logger))
    logger.debug("✅ AuthMiddleware зарегистрирован.")

    dp.message.middleware(BannedCheckMiddleware(logger=logger))
    logger.debug("✅ BannedCheckMiddleware зарегистрирован.")

    dp.message.middleware(TfaMiddleware(logger=logger))
    logger.debug("✅ TfaMiddleware зарегистрирован.")

    dp.message.middleware(RoleMiddleware(
        logger=logger,
        required_roles=["admin", "moderator"]
    ))
    logger.debug("✅ RoleMiddleware зарегистрирован (admin, moderator).")

    # Внедрение зависимостей
    dp.message.middleware(InjectMiddleware("db", db_sessionmaker, logger))
    dp.message.middleware(InjectMiddleware("settings", settings, logger))
    dp.message.middleware(InjectMiddleware("logger", logger, logger))

    logger.debug("✅ InjectMiddleware: db, settings, logger зарегистрированы.")

    if redis:
        dp.message.middleware(InjectMiddleware("redis", redis, logger))
        logger.debug("✅ InjectMiddleware: redis зарегистрирован.")

    logger.info("🛠 Middleware успешно зарегистрированы.")
