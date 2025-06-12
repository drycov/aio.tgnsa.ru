from loguru import logger
import sys
import logging
from pathlib import Path


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


class LoggerManager:
    def __init__(self, name: str = "app", debug: bool = False):
        self.name = name
        self.debug = debug
        self.log_dir = Path(__file__).resolve().parent.parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{self.name}.log"

        self._configure()

    def _configure(self):
        # Очистка стандартных логгеров
        logging.root.handlers = []
        for logger_name in logging.root.manager.loggerDict.keys():
            logging.getLogger(logger_name).handlers = []

        # Настройка loguru
        logger.remove()

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

        logger.add(
            self.log_file,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            level="DEBUG" if self.debug else "INFO",
            encoding="utf-8",
        )

        logging.basicConfig(handlers=[InterceptHandler()], level=0)

    def get_logger(self):
        return logger.bind(name=self.name)
