import inspect
from typing import Any, Dict, Optional

from aiogram import BaseMiddleware, Dispatcher
from pydantic_settings import BaseSettings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.middlewares import (auth, banned, command_log, profiler, role,
                                 superuser, tfa)
from app.core.utils.logger_manager import LoggerManager


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


def _collect_middlewares_from_module(module, logger: LoggerManager, **kwargs) -> Dict[str, BaseMiddleware]:
    """
    Автоматически собирает middleware-классы из модуля.
    Класс должен быть наследником BaseMiddleware и иметь __init__(**kwargs)
    """
    middlewares = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseMiddleware) and obj is not BaseMiddleware:
            try:
                instance = obj(logger=logger, **kwargs)
                middlewares[name] = instance
                logger.debug(f"🧩 Найден middleware: {name}")
            except Exception as e:
                logger.warning(
                    f"⚠️ Не удалось инициализировать middleware {name}: {e}")
    return middlewares


def register_middlewares(
    dp: Dispatcher,
    *,
    db_sessionmaker: async_sessionmaker,
    settings: BaseSettings,
    logger: LoggerManager,
    redis: Optional[Redis] = None,
    role_middleware_roles: Optional[list[str]] = None,
    additional_middlewares: Optional[Dict[str, Any]] = None,
):
    """
    Регистрирует middleware слоя приложения:
    - Автоматически собирает middleware из модулей
    - Инъецирует зависимости
    """
    logger.debug("🔧 Регистрация middleware...")

    # RoleMiddleware с ручной инициализацией (требуются роли)
    try:
        commandLog = command_log.CommandLoggingMiddleware(
            logger=logger,
        )
        dp.message.middleware(commandLog)
        logger.debug(
            f"✅ commandLog зарегистрирован ({commandLog or '[]'}).")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка регистрации CommandLoggingMiddleware: {e}")

    # Superuser всегда первый, чтобы пропускать остальные
    try:
        dp.message.middleware(
            superuser.SuperuserBypassMiddleware(
                superusers=settings.bot.SUPERUSERS, logger=logger)
        )
        logger.debug("✅ SuperuserBypassMiddleware зарегистрирован первым.")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка регистрации SuperuserBypassMiddleware: {e}")

    # Авто-регистрация из модулей
    modules = [profiler, auth, banned, tfa]
    for module in modules:
        mws = _collect_middlewares_from_module(module, logger=logger)
        for name, mw in mws.items():
            dp.message.middleware(mw)
            logger.debug(f"✅ Middleware {name} зарегистрирован.")

    # RoleMiddleware с ручной инициализацией (требуются роли)
    try:
        role_middleware = role.RoleMiddleware(
            required_roles=role_middleware_roles or [],
            logger=logger,
        )
        dp.message.middleware(role_middleware)
        logger.debug(
            f"✅ RoleMiddleware зарегистрирован ({role_middleware_roles or '[]'}).")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка регистрации RoleMiddleware: {e}")

    # Инъекция зависимостей
    dependencies = {
        "db": db_sessionmaker,
        "settings": settings,
        "logger": logger,
    }
    if redis:
        dependencies["redis"] = redis

    for key, value in dependencies.items():
        dp.message.middleware(InjectMiddleware(key, value, logger))
        logger.debug(f"✅ InjectMiddleware: {key} зарегистрирован.")

    # Кастомные
    if additional_middlewares:
        for name, middleware in additional_middlewares.items():
            dp.message.middleware(middleware)
            logger.debug(f"✅ CustomMiddleware: {name} зарегистрирован.")

    logger.info("🛠 Middleware успешно зарегистрированы.")
