# main.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot import handlers
from bot.constants import Messages
from config import Config
from bot.utils.logger import logger  # Импортируем настроенный логгер

bot = Bot(token=Config.API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


async def main():
    # Подключение маршрутизатора команд
    router = handlers.get_handlers_router()  # Получаем маршрутизатор для регистрации обработчиков
    dp.include_router(router)

    # Удаление вебхука и начало поллинга
    logger.info(Messages.DELETE_WEBHOOK.value)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    logger.info(Messages.START_BOT)


async def graceful_shutdown():
    """Функция для корректного завершения работы бота."""
    logger.info(Messages.SHUTDOWN_BOT.value)
    await dp.storage.close()
    await bot.session.close()  # Закрываем сессию бота
    logger.info(Messages.BOT_SHUTDOWN_COMPLETE.value)


# Запуск бота
if __name__ == "__main__":
    logger.info(Messages.START_BOT_MODULE.value)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning(Messages.SHUTDOWN_SIGNAL.value)
        asyncio.run(graceful_shutdown())
