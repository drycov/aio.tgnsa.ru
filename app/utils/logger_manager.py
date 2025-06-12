import logging
import os
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not os.access(LOG_DIR, os.W_OK):
        raise PermissionError
except:
    LOG_DIR = Path("/tmp/tgnms_logs")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"⚠️ Переключение логирования в {LOG_DIR}", file=sys.stderr)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(
            level, record.getMessage())


class LoggerManager:
    def __init__(self, name: str = "app", debug: bool = False):
        self.name = name
        self.debug = debug
        self.log_file_path = LOG_DIR / f"{self.name}.log"

        self._setup_logger()

    def _setup_logger(self):
        logger.remove()

        # Консольный лог
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            level="DEBUG" if self.debug else "INFO",
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
        )

        # Файловый лог
        logger.add(
            self.log_file_path,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            level="DEBUG" if self.debug else "INFO",
            encoding="utf-8"
        )

        logging.root.handlers = [InterceptHandler()]
        logging.root.setLevel(0)

    def get_logger(self):
        return logger.bind(name=self.name)
