from datetime import timedelta
import inspect
from typing import Any, Dict, List, Optional, Type

from aiogram import BaseMiddleware, Dispatcher
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.middlewares.role import RoleMiddleware
from app.bot.middlewares.superuser import SuperuserBypassMiddleware
from app.bot.middlewares.throttling import SmartRateLimitMiddleware
from app.core.config import Settings, settings
from app.core.utils.logger_manager import LoggerManager


class MiddlewareConfig(BaseModel):
    """Конфигурация middleware"""
    rate_limit: float = 1.0
    superusers: List[int] = []
    role_access: Dict[str, List[str]] = {}
    enable_profiler: bool = False
    enable_tfa: bool = False
    max_spam:int = 5


class DependencyInjector(BaseMiddleware):
    """Универсальный инжектор зависимостей"""

    def __init__(self, **dependencies):
        self.dependencies = dependencies

    async def __call__(self, handler, event, data):
        data.update(self.dependencies)
        return await handler(event, data)


class MiddlewareRegistry:
    """Централизованная система регистрации middleware"""

    def __init__(
        self,
        dp: Dispatcher,
        db_sessionmaker: async_sessionmaker,
        settings: BaseModel,
        logger: LoggerManager,
        redis: Optional[Redis] = None,
        config: Optional[MiddlewareConfig] = None
    ):
        self.dp = dp
        self.logger = logger
        self.config = config or MiddlewareConfig()

        self.core_dependencies = {
            "db": db_sessionmaker,
            "settings": settings,
            "logger": logger,
            "redis": redis,
            "config": self.config
        }

        # Порядок имеет значение!
        self.middleware_priority = [
            "SuperuserBypassMiddleware",
            "SmartRateLimitMiddleware",
            "CommandLoggingMiddleware",
            "RoleMiddleware",
            "AuthMiddleware",
            "BannedUserMiddleware",
            "TFAMiddleware",
            "ProfilerMiddleware",
        ]

    def _init_middleware(self, middleware_class: Type[BaseMiddleware], **kwargs) -> Optional[BaseMiddleware]:
        """Инициализация middleware с обработкой ошибок"""
        try:
            kwargs["logger"] = self.logger
            return middleware_class(**kwargs)
        except Exception as e:
            self.logger.error(
                f"Middleware init failed for {middleware_class.__name__}: {e}")
            return None

    async def register(self):
        """Основной метод регистрации middleware"""
        self.logger.info("🛠 Starting middleware registration...")

        # 1. Регистрация зависимостей
        self.dp.message.middleware(
            DependencyInjector(**self.core_dependencies))
        self.logger.debug("✅ Core dependencies injected")

        # 2. Регистрация middleware по приоритету
        registered = set()

        for mw_name in self.middleware_priority:
            if mw_instance := self._get_middleware_instance(mw_name):
                self.dp.message.middleware(mw_instance)
                registered.add(mw_name)
                self.logger.debug(f"✅ {mw_name} registered")

        # 3. Проверка что все обязательные middleware зарегистрированы
        self._validate_registration(registered)

        self.logger.info(
            f"🏁 Completed! Registered {len(registered)} middleware")

    def _get_middleware_instance(self, mw_name: str) -> Optional[BaseMiddleware]:
        """Фабрика для создания экземпляров middleware"""
        if mw_name == "SuperuserBypassMiddleware":
            return self._init_middleware(
                SuperuserBypassMiddleware,
                superusers=self.config.superusers
            )

        if mw_name == "SmartRateLimitMiddleware":
            return self._init_middleware(
                SmartRateLimitMiddleware,
                rate_limit=self.config.rate_limit,
                max_spam=self.config.max_spam,
                cooldown=timedelta(minutes=5),
                exempt_user_ids=self.config.superusers
            )

        if mw_name == "RoleMiddleware":
            return self._init_middleware(
                RoleMiddleware,
                required_roles=self.config.role_access
            )

        # Для остальных middleware используем автоматическое создание
        try:
            if module := globals().get(mw_name.replace("Middleware", "").lower()):
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name == mw_name and issubclass(obj, BaseMiddleware):
                        return self._init_middleware(obj)
        except Exception as e:
            self.logger.warning(f"Auto-registration failed for {mw_name}: {e}")

        return None

    def _validate_registration(self, registered: set):
        """Проверка что все критические middleware зарегистрированы"""
        critical_middleware = {
            "SuperuserBypassMiddleware",
            "SmartRateLimitMiddleware",
            "RoleMiddleware"
        }

        if missing := critical_middleware - registered:
            self.logger.error(f"Critical middleware missing: {missing}")
            raise RuntimeError(
                f"Failed to register critical middleware: {missing}")


# Пример использования
async def setup_middleware(
    dp: Dispatcher,
    db_sessionmaker: async_sessionmaker,
    settings: Settings,
    logger: LoggerManager,
    redis: Optional[Redis] = None
):
    """Инициализация middleware системы"""
    config = MiddlewareConfig(
        superusers=settings.bot.SUPERUSERS,
        rate_limit=settings.bot.RATE_LIMIT,
        role_access=settings.bot.ROLE_ACCESS,
        enable_tfa=settings.security.TFA_ENABLE
    )

    registry = MiddlewareRegistry(
        dp=dp,
        db_sessionmaker=db_sessionmaker,
        settings=settings,
        logger=logger,
        redis=redis,
        config=config
    )

    await registry.register()
