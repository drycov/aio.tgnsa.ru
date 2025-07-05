import logging
from typing import Optional, Union
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Кастомные уровни логирования
CUSTOM_LOG_LEVELS = {
    "TRACE": 5,
    "NOTICE": 21,
    "SUCCESS": 25,
}

# Тема для Rich
RICH_THEME = Theme(
    {
        "logging.level.trace": "dim white on black",
        "logging.level.notice": "bold magenta",
        "logging.level.success": "bold green",
        "logging.level.debug": "dim blue",
        "logging.level.info": "bold cyan",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold white on red",
    }
)


class BoundLogger(logging.Logger):
    """Логгер с поддержкой метода bind()"""

    def bind(self, **kwargs) -> "ContextLogger":
        return ContextLogger(self, kwargs)


class ContextLogger(logging.LoggerAdapter):
    """Адаптер логгера с контекстом и поддержкой bind()"""

    def bind(self, **kwargs) -> "ContextLogger":
        merged = {**self.extra, **kwargs}
        return ContextLogger(self.logger, merged)

    def process(self, msg, kwargs):
        if self.extra:
            kwargs["extra"] = {**kwargs.get("extra", {}), **self.extra}
        return msg, kwargs

class ExtraContextFilter(logging.Filter):
    def filter(self, record):
        record.extra_context = ""
        for key, value in getattr(record, 'extra', {}).items():
            record.extra_context += f" {key}={value}"
        return True

def _patch_logger_class():
    """Добавляет кастомные уровни и метод bind к классу Logger"""
    for name, level in CUSTOM_LOG_LEVELS.items():
        logging.addLevelName(level, name)

        def make_log_method(level_name, level_num):
            def log_method(self, message, *args, **kwargs):
                if self.isEnabledFor(level_num):
                    self._log(level_num, message, args, **kwargs)

            return log_method

        setattr(logging.Logger, name.lower(), make_log_method(name, level))
    logging.Logger.bind = lambda self, **kwargs: ContextLogger(self, kwargs)


_patch_logger_class()


class LoggerManager:
    """Менеджер логгеров с поддержкой Rich и файлового логирования"""

    def __init__(
        self,
        name: str = "app",
        debug: bool = False,
        log_dir: Optional[Union[str, Path]] = None,
        log_level: Optional[Union[str, int]] = None,
        enable_file: bool = True,
        enable_console: bool = True,
        file_size: int = 10 * 1024 * 1024,
        backups: int = 5,
    ):
        self.name = name
        self.debug = debug
        self.log_level = log_level or ("DEBUG" if debug else "INFO")
        self.enable_file = enable_file
        self.enable_console = enable_console
        self.file_size = file_size
        self.backups = backups
        self.log_dir = log_dir or "logs"
        self._logger = self._configure_logger()

# --- Изменим метод _configure_logger() ---

    def _configure_logger(self) -> BoundLogger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        logger.handlers.clear()

        # Основной formatter
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Консольный formatter для Rich
        console_formatter = logging.Formatter(
            "[%(asctime)s][%(name)s] %(message)s%(extra_context)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Файловый обработчик
        if self.enable_file:
            log_dir = self._ensure_log_dir()
            file_handler = RotatingFileHandler(
                log_dir / f"{self.name}.log",
                maxBytes=self.file_size,
                backupCount=self.backups,
                encoding="utf-8",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Консольный обработчик с Rich
        if self.enable_console:
            console = Console(theme=RICH_THEME)
            rich_handler = RichHandler(
                console=console,
                show_time=True,
                show_level=True,
                show_path=False,
                rich_tracebacks=True,
                tracebacks_show_locals=self.debug,
            )
            rich_handler.setFormatter(console_formatter)
            rich_handler.addFilter(ExtraContextFilter())
            logger.addHandler(rich_handler)

        logger.__class__ = BoundLogger
        return logger

    def _ensure_log_dir(self) -> Path:
        log_dir = Path(self.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_logger(self) -> BoundLogger:
        return self._logger


# Пример использования
if __name__ == "__main__":
    logger = LoggerManager(name="my_app", debug=True).get_logger()
    logger.info("This is an info message")
    logger.bind(user_id=123, request_id="abc").info("Processing request")
    logger.success("Operation completed successfully")
    logger.notice("Important notice")
    logger.trace("Detailed trace information")
