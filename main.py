# main.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from app import setup_bot, start_bot, graceful_shutdown
from app.constants import Messages
from app.utils.logger import logger  # Настроенный логгер

if __name__ == "__main__":
    logger.info(Messages.START_BOT_MODULE.value)

    try:
        setup_bot()  # Подключение обработчиков и настройка бота
        asyncio.run(start_bot())  # Запуск основного процесса бота
    except (KeyboardInterrupt, SystemExit):
        logger.warning(Messages.SHUTDOWN_SIGNAL.value)
        asyncio.run(graceful_shutdown())  # Корректное завершение
