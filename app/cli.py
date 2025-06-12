import argparse
import os
import sys


def run():
    parser = argparse.ArgumentParser(description="TGNMS entrypoint")

    # Взаимоисключающая группа флагов
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bot", action="store_true", help="Run Telegram bot")
    group.add_argument("--api", action="store_true", help="Run API server")
    group.add_argument("--scheduler", action="store_true",
                       help="Run background scheduler")

    # Общие флаги
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")

    args = parser.parse_args()

    # Установка переменной окружения до инициализации конфигурации
    
    if args.debug:
        os.environ["DEBUG"] = "True"

    if args.bot:
        os.environ["APP_ROLE"] = "bot"
    elif args.api:
        os.environ["APP_ROLE"] = "api"
    elif args.scheduler:
        os.environ["APP_ROLE"] = "scheduler"

    # Импорт после установки окружения
    from .api.server import run_api
    from .bot.runner import run_bot
    from .core.config import logger
    from .scheduler.jobs import run_scheduler

    # Диспетчеризация по роли
    if args.bot:
        logger.info("🚀 Запуск Telegram-бота...")
        run_bot()
    elif args.api:
        logger.info("🚀 Запуск API-сервера...")
        run_api()
    elif args.scheduler:
        logger.info("🚀 Запуск планировщика задач...")
        run_scheduler()
    else:
        logger.error("❌ Не удалось определить роль приложения.")
        sys.exit(1)
