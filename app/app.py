# bot_module.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app import handlers
from app.constants import Messages
from config import Config
from app.utils.logger import logger  # Настроенный логгер

bot = Bot(token=Config.API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


def setup_bot():
    """
    Настройка бота и регистрация обработчиков.
    """
    # Подключение маршрутизатора команд
    router = handlers.get_handlers_router()
    dp.include_router(router)


async def start_bot():
    """
    Запускает бота и начинает обработку сообщений.
    """
    # Удаление вебхука и начало поллинга
    logger.info(Messages.DELETE_WEBHOOK.value)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    logger.info(Messages.START_BOT.value)


async def graceful_shutdown():
    """
    Функция для корректного завершения работы бота.
    """
    logger.info(Messages.SHUTDOWN_BOT.value)
    await dp.storage.close()
    await bot.session.close()
    logger.info(Messages.BOT_SHUTDOWN_COMPLETE.value)
