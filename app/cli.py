# app/cli.py
import sys
import argparse
from .bot.runner import run_bot
from .api.server import run_api
from core.config import logger


def run():
    parser = argparse.ArgumentParser(description="TGNMS entrypoint")
    parser.add_argument("--bot", action="store_true", help="Run Telegram bot")
    parser.add_argument("--api", action="store_true", help="Run API server")
    args = parser.parse_args()

    if args.bot:
        run_bot()
    elif args.api:
        run_api()
    else:
        logger.info("❌ Укажите флаг: --bot или --api")
        sys.exit(1)
