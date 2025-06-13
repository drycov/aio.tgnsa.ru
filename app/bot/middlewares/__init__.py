from typing import Any, Dict, List, Optional, Tuple

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
    def __init__(self, key: str, value: Any, logger: Optional[LoggerManager] = None):
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
    redis: Optional[Redis] = None,
):
    """Регистрирует все middleware в нужном порядке."""

    logger.debug("🔧 Регистрация middleware...")
    
    # Группировка middleware по категориям для более организованной регистрации
    technical_middlewares = [
        ("ProfilerMiddleware", ProfilerMiddleware(logger=logger)),
        ("CommandLoggingMiddleware", CommandLoggingMiddleware(logger=logger)),
    ]
    
    business_middlewares = [
        ("AuthMiddleware", AuthMiddleware(logger=logger)),
        ("BannedCheckMiddleware", BannedCheckMiddleware(logger=logger)),
        ("TfaMiddleware", TfaMiddleware(logger=logger)),
        ("RoleMiddleware", RoleMiddleware(logger=logger, required_roles=["admin", "moderator"])),
    ]
    
    # Базовые зависимости для внедрения
    dependencies = [
        ("db", db_sessionmaker),
        ("settings", settings),
        ("logger", logger),
    ]
    
    # Регистрация middleware по группам
    for name, middleware in technical_middlewares:
        dp.message.middleware(middleware)
        logger.debug(f"✅ {name} зарегистрирован.")
        
    for name, middleware in business_middlewares:
        dp.message.middleware(middleware)
        logger.debug(f"✅ {name} зарегистрирован" + (" (admin, moderator)." if name == "RoleMiddleware" else "."))
    
    # Регистрация инъекций зависимостей
    for key, value in dependencies:
        dp.message.middleware(InjectMiddleware(key, value, logger))
    logger.debug("✅ InjectMiddleware: db, settings, logger зарегистрированы.")
    
    # Опциональная регистрация Redis
    if redis:
        dp.message.middleware(InjectMiddleware("redis", redis, logger))
        logger.debug("✅ InjectMiddleware: redis зарегистрирован.")

    logger.info("🛠 Middleware успешно зарегистрированы.")