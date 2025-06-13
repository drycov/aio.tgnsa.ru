import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core import initialize_storage
from app.core.config import logger, settings


# === Инициализация ===
storage = initialize_storage()
bot = Bot(token=settings.bot.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# Подключение middlewares, filters, routers
def setup_dispatcher():
    # from app.bot.middlewares import register_middlewares
    # from app.bot.routers import register_routers

    # register_middlewares(dp)
    # register_routers(dp)
    pass


async def on_startup():
    logger.info("🟢 Бот запускается...")

async def on_shutdown():
    logger.info("🛑 Завершается работа бота...")
    await bot.session.close()
    await storage.close()

async def main():
    setup_dispatcher()
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
