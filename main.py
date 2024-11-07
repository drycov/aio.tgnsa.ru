# main.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
from pathlib import Path

import firebase_admin
from firebase_admin import credentials

from app import setup_bot, start_bot, graceful_shutdown
from app.constants import Messages
from app.utils.logger_instance import app_logger
from config import Config
from housekeeper import Housekeeper

# Получение экземпляра логгера
# app_logger = get_app_logger()
housekeeper = Housekeeper()

# Инициализация Firebase
try:
    if not firebase_admin._apps:
        serviceAccountKey = Path(Config.BASE_DIR) / "serviceAccountKey.json"
        app_logger.info(f"Начало инициализации Firebase с файлом ключа: {serviceAccountKey}")

        cred = credentials.Certificate(serviceAccountKey)
        database_url = Config.FIREBASE_DATABASE_URL
        if not database_url:
            raise ValueError("FIREBASE_DATABASE_URL не задана. Пожалуйста, укажите URL базы данных в .env файле.")

        # Инициализация Firebase с указанием URL базы данных
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        app_logger.info("Firebase успешно инициализирован")
    else:
        app_logger.info("Firebase уже инициализирован")
except Exception as e:
    app_logger.error(f"Ошибка при инициализации Firebase: {e}")
    sys.exit(1)


async def on_startup(dispatcher):
    # Запускаем фоновую задачу Housekeeper для очистки старых данных
    asyncio.create_task(housekeeper.run())  # Запускаем Housekeeper в фоновом режиме


if __name__ == "__main__":
    app_logger.info(Messages.START_BOT_MODULE.value)

    try:
        asyncio.run(housekeeper.report_status())

        setup_bot()  # Подключение обработчиков и настройка бота
        asyncio.run(start_bot(on_startup=on_startup))  # Запуск основного процесса бота с вызовом on_startup

    except (KeyboardInterrupt, SystemExit):
        app_logger.warning(Messages.SHUTDOWN_SIGNAL.value)
        asyncio.run(graceful_shutdown())  # Корректное завершение
