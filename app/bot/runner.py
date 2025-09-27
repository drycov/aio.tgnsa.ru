# app/core/bot_manager.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core import initialize_storage
from app.core.applcm_manager import AppLifecycleManager
from app.core.config import APP_DIR, BASE_DIR, settings
from app.core.db import get_sessionmaker
from app.core.plugin_manager.manager import PluginManager
from app.core.logging_setup import logger


class BotManager:
    name = "BotManager"

    def __init__(self, lifecycle_manager: AppLifecycleManager):
        self.lifecycle_manager = lifecycle_manager
        self.logger = logger.bind(component=self.__class__.__name__)
        self.storage = initialize_storage()
        self.session = get_sessionmaker()

        token = settings.bot.TOKEN.get_secret_value()
        if not token:
            raise RuntimeError("❌ Не найден TELEGRAM TOKEN в настройках")

        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.dp = Dispatcher(storage=self.storage, session=self.session, bot=self.bot)

        # Lifecycle hooks
        lifecycle_manager.on_startup(name="bot_startup")(self.on_startup)
        lifecycle_manager.on_shutdown(name="bot_shutdown")(self.on_shutdown)

        self.logger.info(f"[{self.name}] инициализирован")
        self.logger.debug(f"[{self.name}]📦 Версия приложения: {settings.VERSION}")
        self.logger.debug(f"[{self.name}]📂 Путь к приложению: {APP_DIR}")
        self.logger.debug(f"[{self.name}]📂 Базовый путь: {BASE_DIR}")
        self.logger.debug(f"[{self.name}]storage: {self.storage.__class__.__name__}")
        self.logger.debug(f"[{self.name}]session: {self.session.__class__.__name__}")

    async def setup(self):
        """Регистрация middlewares, фильтров, хендлеров, плагинов."""
        from app.bot.handlers import register_handlers
        from app.bot.middlewares.registry import setup_middleware

        await setup_middleware(
            self.dp, db_sessionmaker=self.session, settings=settings, logger=self.logger
        )
        register_handlers(
            self.dp, db_sessionmaker=self.session, settings=settings, logger=self.logger
        )

        await self.setup_plugins()
        
    async def setup_plugins(self):
        """Подключает плагины и регистрирует их в aiogram."""
        pm = PluginManager.get_instance()

        if not pm.is_initialized:
            self.logger.info("🔌 Первичная инициализация плагинов...")
            pm.full_load_cycle(settings)

        for plugin in pm.all_plugins().values():
            self._register_plugin(plugin)

    def _register_plugin(self, plugin):
        """Безопасная регистрация aiogram-хендлеров и middleware у плагина."""
        meta = getattr(plugin, "meta", None)
        pname = getattr(meta, "name", plugin.__class__.__name__)

        try:
            if hasattr(plugin, "register_aiogram"):
                plugin.register_aiogram(self.dp)
                self.logger.info(f"🔗 [{pname}] зарегистрировал роутеры")

            if hasattr(plugin, "register_middlewares"):
                plugin.register_middlewares(self.dp)
                self.logger.info(f"🧩 [{pname}] зарегистрировал middleware")

            if hasattr(plugin, "register_callbacks"):
                plugin.register_callbacks(self.dp)
                self.logger.info(f"🎯 [{pname}] зарегистрировал callbacks")

            if hasattr(plugin, "register_inline_query"):
                plugin.register_inline_query(self.dp)
                self.logger.info(f"🔍 [{pname}] зарегистрировал inline-query")

            self.logger.info(f"✅ [{pname}] успешно подключён")
        except Exception as e:
            self.logger.error(f"❌ Ошибка регистрации [{pname}]: {e}", exc_info=True)


    async def on_startup(self):
        self.logger.info("🟢 Бот запускается...")
        self.logger.info(f"📦 Версия приложения: {settings.VERSION}")

    async def on_shutdown(self):
        self.logger.info("🛑 Завершается работа бота...")
        await self.dp.fsm.storage.close()
        # await self.dp.fsm.storage.wait_closed()
        await self.bot.session.close()
        await self.lifecycle_manager.shutdown()
        self.logger.info("✅ Shutdown завершён")

    async def start_polling(self):
        """Основной цикл aiogram."""
        await self.setup()
        await self.lifecycle_manager.startup()

        try:
            await self.dp.start_polling(self.bot)
        except asyncio.CancelledError:
            self.logger.warning("❗️ Polling отменён.")
        except Exception as ex:
            self.logger.exception(f"💥 Необработанная ошибка: {ex}")
        finally:
            await self.on_shutdown()

    def run(self):
        """Запуск Polling."""
        try:
            asyncio.run(self.start_polling())
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("⏹ Завершение по сигналу прерывания.")


def run_bot(lifecycle: AppLifecycleManager):
    BotManager(lifecycle).run()
