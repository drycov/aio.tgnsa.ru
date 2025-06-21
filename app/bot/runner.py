import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import initialize_storage
from app.core.config import logger, settings
from app.core.db import get_session
from app.plugins.manager import PluginManager

# === Инициализация ===
storage = initialize_storage()
session = get_session()
bot = Bot(token=settings.bot.TOKEN.get_secret_value(),
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage, session=session, bot=bot)

# Подключение middlewares, filters, routers



def setup_plugins(dp: Dispatcher):
    manager = PluginManager.create_once()
    manager.load_all()
    manager.init_all(settings)
    manager.register_aiogram(dp)


async def setup_dispatcher():
    from app.bot.handlers import register_handlers
    from app.bot.middlewares.registry import setup_middleware

    await setup_middleware(dp, db_sessionmaker=session,
                           settings=settings, logger=logger)
    register_handlers(dp, db_sessionmaker=session,
                      settings=settings, logger=logger)
    setup_plugins(dp)


async def on_startup():
    logger.info("🟢 Бот запускается...")


async def on_shutdown():
    logger.info("🛑 Завершается работа бота...")
    await bot.session.close()
    await storage.close()


async def main():
    await setup_dispatcher()
    await on_startup()
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.warning("❗️ Polling отменён.")
    except Exception as ex:
        logger.exception(f"💥 Необработанная ошибка: {ex}")
    finally:
        await on_shutdown()
        logger.info("✅ Бот успешно остановлен.")


def run_bot():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹ Завершение по сигналу прерывания.")
