import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core import initialize_storage
from app.core.applcm_manager import AppLifecycleManager
from app.core.config import APP_DIR, BASE_DIR, settings, logger
from app.core.db import get_sessionmaker
from app.core.plugin_manager.manager import PluginManager


class BotManager:
    name = "BotManager"
    def __init__(self, lifecycle_manager: AppLifecycleManager):
        self.lifecycle_manager = lifecycle_manager
        self.logger = logger.bind(component=self.name)

        self.storage = initialize_storage()
        self.session = get_sessionmaker()
        self.bot = Bot(
            token=settings.bot.TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.dp = Dispatcher(storage=self.storage, session=self.session, bot=self.bot)

        # Регистрация lifecycle hooks
        lifecycle_manager.on_startup(name="bot_startup")(self.on_startup)
        lifecycle_manager.on_shutdown(name="bot_shutdown")(self.on_shutdown)
        self.logger.info(f"[{self.name}] инициализирован")
        self.logger.info(f"[{self.name}]📦 Версия приложения: {settings.VERSION}")
        self.logger.info(f"[{self.name}]📂 Путь к приложению: {APP_DIR}")
        self.logger.info(f"[{self.name}]📂 Базовый путь: {BASE_DIR}")
        self.logger.info(f"[{self.name}]storage: {self.storage.__class__.__name__}")
        self.logger.info(f"[{self.name}]session: {self.session.__class__.__name__}")



    async def setup(self):
        # Регистрация middlewares, фильтров, хендлеров
        from app.bot.handlers import register_handlers
        from app.bot.middlewares.registry import setup_middleware

        await setup_middleware(
            self.dp, db_sessionmaker=self.session, settings=settings, logger=logger
        )
        register_handlers(
            self.dp, db_sessionmaker=self.session, settings=settings, logger=logger
        )

        # Подключаем плагины
        self.setup_plugins()

    def setup_plugins(self):
        pm = PluginManager()
        pm.ensure_ready(settings)
        if not pm.is_initialized:
            logger.warning("🔌 Плагины не инициализированы. Инициализация...")
            pm.ensure_ready(settings)
        for plugin in pm.all_plugins().values():
            plugin.register_aiogram(self.dp)  # регистрация своих роутеров

    async def on_startup(self):
        logger.info("🟢 Бот запускается...")
        logger.info(f"📦 Версия приложения: {settings.VERSION}")

    async def on_shutdown(self):
        logger.info("🛑 Завершается работа бота...")
        await self.bot.session.close()
        await self.storage.close()

    async def start_polling(self):
        await self.setup()
        await self.lifecycle_manager.startup()

        try:
            await self.dp.start_polling(self.bot)
        except asyncio.CancelledError:
            logger.warning("❗️ Polling отменён.")
        except Exception as ex:
            logger.exception(f"💥 Необработанная ошибка: {ex}")
        finally:
            await self.lifecycle_manager.shutdown()
            logger.info("✅ Бот успешно остановлен.")

    def run(self):
        import asyncio

        try:
            asyncio.run(self.start_polling())
        except (KeyboardInterrupt, SystemExit):
            logger.info("⏹ Завершение по сигналу прерывания.")


def run_bot(lifecycle: AppLifecycleManager):
    bot_manager = BotManager(lifecycle)
    bot_manager.run()
