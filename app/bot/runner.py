import asyncio

from aiogram import Bot, Dispatcher

from app.core.config import logger, settings

bot = Bot(token=settings.bot.TOKEN)
dp = Dispatcher()


async def main():
    logger.info("🤖 Запуск бота...")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.warning("Polling отменён.")
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")


def run_bot():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹ Завершение по сигналу прерывания.")
