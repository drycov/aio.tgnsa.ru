import argparse
import os
import sys

def run():
    parser = argparse.ArgumentParser(description="TGNMS entrypoint")
    parser.add_argument("--bot", action="store_true", help="Run Telegram bot")
    parser.add_argument("--api", action="store_true", help="Run API server")
    args = parser.parse_args()

    # Установка роли до импорта конфигурации и логгера
    if args.bot:
        os.environ["APP_ROLE"] = "bot"
    elif args.api:
        os.environ["APP_ROLE"] = "api"
    else:
        print("❌ Укажите флаг: --bot или --api")
        sys.exit(1)

    # Теперь, когда окружение установлено, можно импортировать
    from .core.config import logger
    from .bot.runner import run_bot
    from .api.server import run_api

    if args.bot:
        run_bot()
    elif args.api:
        run_api()
