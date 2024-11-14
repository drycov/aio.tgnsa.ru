import asyncio
import sys
from pathlib import Path

import firebase_admin
from aiogram import Bot, Dispatcher
from firebase_admin import credentials

from app import start_bot, graceful_shutdown
from app.constants import Messages
from app.utils.logger_instance import app_logger
from config import Config
from healthy import Healthy
from healthy_api import run as run_health_api
from housekeeper import Housekeeper

# Настройка бота и диспетчера
bot = Bot(token=Config.API_TOKEN)
dp = Dispatcher()

# Создание экземпляров для фоновых задач
housekeeper = Housekeeper()
health_checker = Healthy()

# Инициализация Firebase
try:
    if not firebase_admin._apps:
        serviceAccountKey = Path(Config.BASE_DIR) / "serviceAccountKey.json"
        app_logger.info(f"Начало инициализации Firebase с файлом ключа: {serviceAccountKey}")

        # Проверка существования файла
        if not serviceAccountKey.exists():
            app_logger.error(f"Файл serviceAccountKey.json не найден по пути: {serviceAccountKey}")
            sys.exit(1)

        cred = credentials.Certificate(serviceAccountKey)
        firebase_admin.initialize_app(cred, {
            'databaseURL': Config.FIREBASE_DATABASE_URL
        })
        app_logger.info("Firebase успешно инициализирован")
except FileNotFoundError as fnf_error:
    app_logger.error(f"Файл serviceAccountKey.json не найден: {fnf_error}")
    sys.exit(1)
except Exception as e:
    app_logger.error(f"Ошибка при инициализации Firebase: {e}")
    sys.exit(1)


async def on_startup():
    """
    Функция, выполняющая действия при старте бота.
    Запускает фоновые задачи для Health Checker и Housekeeper.
    """
    # Запуск Health API в отдельном потоке, если мониторинг включен
    if Config.HEALTHY_CHECK_ENABLE:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, run_health_api)  # Health API сервер

    # Запуск фоновых задач
    asyncio.create_task(housekeeper.run())
    if Config.HEALTHY_CHECK_ENABLE:
        asyncio.create_task(health_checker.run())  # Health Checker
    app_logger.info("Фоновые задачи Housekeeper и Health Checker запущены")


async def main():
    """
    Главная функция запуска бота с учетом запуска фоновых задач.
    """
    # Запуск бота с on_startup
    await start_bot(on_startup=on_startup)


if __name__ == "__main__":
    app_logger.info(Messages.START_BOT_MODULE.value)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Завершаем бота и фоновые задачи при выходе
        asyncio.run(graceful_shutdown())
        app_logger.warning(Messages.SHUTDOWN_SIGNAL.value)
