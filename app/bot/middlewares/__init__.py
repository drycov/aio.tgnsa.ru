# from typing import Any, Dict, Optional, Tuple

# from aiogram import Dispatcher
# from pydantic_settings import BaseSettings
# from redis.asyncio import Redis
# from sqlalchemy.ext.asyncio import async_sessionmaker

# from app.bot.middlewares.superuser import SuperuserBypassMiddleware
# from app.core.utils.logger_manager import LoggerManager

# from .auth import AuthMiddleware
# from .banned import BannedCheckMiddleware
# from .command_log import CommandLoggingMiddleware
# from .profiler import ProfilerMiddleware
# from .role import RoleMiddleware
# from .tfa import TfaMiddleware


# class InjectMiddleware:
#     def __init__(self, key: str, value: Any, logger: Optional[LoggerManager] = None):
#         self.key = key
#         self.value = value
#         self.logger = logger

#     async def __call__(self, handler, event, data):
#         data[self.key] = self.value
#         if self.logger:
#             self.logger.debug(f"📦 Значение '{self.key}' внедрено в data.")
#         return await handler(event, data)


# def register_middlewares(
#     dp: Dispatcher,
#     *,
#     db_sessionmaker: async_sessionmaker,
#     settings: BaseSettings,
#     logger: LoggerManager,
#     redis: Optional[Redis] = None,
#     additional_middlewares: Optional[Dict[str, Any]] = None,
# ):
#     """
#     Регистрирует middleware слоя приложения:
#     - Технические (логгирование, профилирование)
#     - Бизнес-логика (аутентификация, роли, TFA)
#     - Инъекции зависимостей (db, settings, redis и др.)
#     """
#     logger.debug("🔧 Регистрация middleware...")

#     # Дополнительные middleware

#     # Технические middleware
#     technical_middlewares = {
#         "ProfilerMiddleware": ProfilerMiddleware(logger=logger),
#         "CommandLoggingMiddleware": CommandLoggingMiddleware(logger=logger),
#     }
#     # Бизнес-логика
#     business_middlewares = {
#         "SuperuserBypassMiddleware": SuperuserBypassMiddleware(superusers=settings.bot.SUPERUSERS, logger=logger),
#         "AuthMiddleware": AuthMiddleware(logger=logger),
#         "BannedCheckMiddleware": BannedCheckMiddleware(logger=logger),
#         "TfaMiddleware": TfaMiddleware(logger=logger),
#         "RoleMiddleware": RoleMiddleware(logger=logger, required_roles=["admin", "moderator"]),
#     }

#     # Инъекции зависимостей
#     dependency_middlewares = {
#         "db": db_sessionmaker,
#         "settings": settings,
#         "logger": logger,
#     }

#     if redis:
#         dependency_middlewares["redis"] = redis

#     # Регистрация технических middleware
#     for name, middleware in technical_middlewares.items():
#         dp.message.middleware(middleware)
#         logger.debug(f"✅ {name} зарегистрирован.")

#     # Регистрация бизнес-middleware
#     for name, middleware in business_middlewares.items():
#         dp.message.middleware(middleware)
#         if name == "RoleMiddleware":
#             logger.debug(f"✅ {name} зарегистрирован (admin, moderator).")
#         else:
#             logger.debug(f"✅ {name} зарегистрирован.")

#     # Инъекция зависимостей
#     for key, value in dependency_middlewares.items():
#         dp.message.middleware(InjectMiddleware(key, value, logger))
#     logger.debug(
#         f"✅ InjectMiddleware: {', '.join(dependency_middlewares.keys())} зарегистрированы.")

#     # Дополнительные кастомные middleware (опционально)
#     if additional_middlewares:
#         for name, middleware in additional_middlewares.items():
#             dp.message.middleware(middleware)
#             logger.debug(f"✅ CustomMiddleware: {name} зарегистрирован.")

#     logger.info("🛠 Middleware успешно зарегистрированы.")
