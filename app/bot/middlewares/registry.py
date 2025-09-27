import inspect
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Type

from aiogram import BaseMiddleware, Dispatcher
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.profiler import ProfilerMiddleware
from app.bot.middlewares.throttling import SmartRateLimitMiddleware
from app.core.config import Settings
from app.core.utils.logger_manager import LoggerManager
import importlib


class MiddlewareConfig(BaseModel):
    """
    rate_limit: float      # Лимит RPS
    superusers: List[int]  # Исключения из throttling
    role_access: Dict      # Ролевой доступ
    enable_profiler: bool  # Профайлер включен/выключен
    enable_tfa: bool       # Включить двухфакторку
    max_spam: int          # Сколько спама допускается
    priorities: Dict[str,int] # Приоритеты middleware (чем меньше число — тем раньше выполняется)
    """
    rate_limit: float = 1.0
    superusers: List[int] = []
    role_access: Dict[str, List[str]] = {}
    enable_profiler: bool = False
    enable_tfa: bool = False
    max_spam: int = 5
    priorities: Dict[str, int] = {}  # 👈 добавлено


class DependencyInjector(BaseMiddleware):
    """Инжектор зависимостей в `data` словарь хендлера."""

    def __init__(self, **dependencies: Any):
        self.dependencies = dependencies

    async def __call__(self, handler, event, data):
        data.update(self.dependencies)
        return await handler(event, data)


class MiddlewareRegistry:
    """Централизованная система регистрации middleware."""

    def __init__(
        self,
        dp: Dispatcher,
        db_sessionmaker: async_sessionmaker,
        settings: Settings,
        logger: LoggerManager,
        redis: Optional[Redis] = None,
        config: Optional[MiddlewareConfig] = None,
    ):
        self.dp = dp
        self.logger = logger
        self.config = config or MiddlewareConfig()
        self.redis = redis
        self.settings = settings

        self.core_dependencies = {
            "db": db_sessionmaker,
            "settings": settings,
            "logger": logger,
            "redis": redis,
            "config": self.config,
        }

        self.middleware_priority = self._build_priority_order()

        # Явно регистрируемые middleware
        # ...
        self.custom_factories: Dict[str, Callable[[], BaseMiddleware]] = {
            "SmartRateLimitMiddleware": lambda: SmartRateLimitMiddleware(
                rate_limit=self.config.rate_limit,
                max_spam=self.config.max_spam,
                cooldown=timedelta(minutes=5),
                exempt_user_ids=self.config.superusers,
                logger=self.logger,
            ),
            "DatabaseMiddleware": lambda: DatabaseMiddleware(
                sessionmaker=self.core_dependencies[
                    "db"
                ],  # ✅ здесь нужный sessionmaker
                logger=self.logger,
                auto_commit=True,  # или False, по политике
            ),
            "ProfilerMiddleware": lambda: ProfilerMiddleware(
                logger=self.logger,
                warn_threshold=1.0,  # можно брать из settings.misc.profiler_threshold
                enable_prometheus=True,  # включаем экспорт метрик
            ),
        }

    def _build_priority_order(self) -> List[str]:
        """Построение списка middleware с учётом приоритета."""
        default = {
            "CommandLoggingMiddleware": 50,
            "SmartRateLimitMiddleware": 10,
            "TFAMiddleware": 30,
            "ProfilerMiddleware": 70,
            "DatabaseMiddleware": 15,
        }

        priorities = {**default, **self.config.priorities}
        return [k for k, _ in sorted(priorities.items(), key=lambda item: item[1])]

    async def register(self) -> None:
        """Регистрация всех middleware."""
        self.logger.info("🔧 Регистрация middleware...")

        # Core dependencies
        self.dp.message.middleware(DependencyInjector(**self.core_dependencies))
        self.logger.debug("✅ DependencyInjector подключен")

        registered: Set[str] = set()

        for mw_name in self.middleware_priority:
            mw = await self._build_middleware(mw_name)
            if mw_name == "ProfilerMiddleware" and not self.config.enable_profiler:
                continue
            if mw_name == "TFAMiddleware" and not self.config.enable_tfa:
                continue
            if mw:
                self.dp.message.middleware(mw)
                self.dp.callback_query.middleware(mw)

                registered.add(mw_name)
                self.logger.debug(f"✅ Middleware зарегистрирован: {mw_name}")

        self._ensure_critical(registered)

        self.logger.info(f"🏁 Завершена регистрация {len(registered)} middleware")

    async def _build_middleware(self, name: str) -> Optional[BaseMiddleware]:
        """Фабрика инициализации middleware по имени."""
        if name in self.custom_factories:
            try:
                return self.custom_factories[name]()
            except Exception as e:
                self.logger.error(f"⚠️ Ошибка инициализации {name}: {e}")
                return None
        return self._auto_resolve(name)

    def _safe_init(
        self, cls: Type[BaseMiddleware], **kwargs
    ) -> Optional[BaseMiddleware]:
        """Безопасная инициализация middleware."""
        try:
            return (
                cls(
                    rate_limit=self.config.rate_limit,
                    max_spam=self.config.max_spam,
                    cooldown=timedelta(minutes=5),
                    exempt_user_ids=self.config.superusers,
                    logger=self.logger,
                    **kwargs,
                )
                if cls is SmartRateLimitMiddleware
                else cls(logger=self.logger, **kwargs)
            )
        except Exception as e:
            self.logger.error(f"⚠️ Ошибка инициализации {cls.__name__}: {e}")
            return None

    def _auto_resolve(self, name: str) -> Optional[BaseMiddleware]:
        module_name = name.replace("Middleware", "").lower()
        try:
            # The line `module = importlib.import_module(f"app.bot.middlewares.{module_name}")` is
            # importing a module dynamically at runtime based on the `module_name` variable. This
            # allows the code to load and use a module whose name is constructed using the
            # `module_name` variable, which is derived from the `name` parameter passed to the
            # `_auto_resolve` method in the `MiddlewareRegistry` class.
            module = importlib.import_module(f"app.bot.middlewares.{module_name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__name__ == name and issubclass(obj, BaseMiddleware):
                    return self._safe_init(obj)
        except Exception as e:
            self.logger.warning(f"❌ Не удалось подключить {name}: {e}")
        return None

    def _ensure_critical(self, registered: Set[str]) -> None:
        """Проверка обязательных middleware."""
        critical = {"SmartRateLimitMiddleware"}
        missing = critical - registered
        if missing:
            self.logger.critical(
                f"❌ Отсутствуют критически важные middleware: {missing}"
            )
            raise RuntimeError(f"Не зарегистрированы middleware: {missing}")


# 🔌 Функция подключения
async def setup_middleware(
    dp: Dispatcher,
    db_sessionmaker: async_sessionmaker,
    settings: Settings,
    logger: LoggerManager,
    redis: Optional[Redis] = None,
) -> None:
    """Инициализация MiddlewareRegistry с приоритетами."""
    config = MiddlewareConfig(
        superusers=settings.bot.SUPERUSERS,
        rate_limit=settings.bot.RATE_LIMIT,
        role_access=settings.bot.ROLE_ACCESS,
        enable_tfa=settings.security.TFA_ENABLE,
        priorities={
            "CommandLoggingMiddleware": 5,
            "SmartRateLimitMiddleware": 10,
            "TFAMiddleware": 50,
            "ProfilerMiddleware": 100,
            "DatabaseMiddleware": 15,
        },
    )

    registry = MiddlewareRegistry(
        dp=dp,
        db_sessionmaker=db_sessionmaker,
        settings=settings,
        logger=logger,
        redis=redis,
        config=config,
    )

    await registry.register()
