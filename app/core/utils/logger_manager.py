import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# === Цветовая тема для Rich ===
RICH_THEME = Theme(
    {
        "logging.level.trace": "dim white",
        "logging.level.notice": "bold magenta",
        "logging.level.success": "bold green",
        "logging.level.debug": "dim blue",
        "logging.level.info": "bold cyan",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold white on red",
        "logging.time": "dim",
        "logging.name": "cyan",
    }
)

# === Кастомные уровни ===
# NOTICE_LEVEL_NUM = 21
# SUCCESS_LEVEL_NUM = 25
# TRACE_LEVEL_NUM = 5

# Определяем кастомные уровни
CUSTOM_LOG_LEVELS = {
    "TRACE": 21,
    "NOTICE": 23,
    "SUCCESS": 25,
}

# logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

# logging.addLevelName(NOTICE_LEVEL_NUM, "NOTICE")
# logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


# === Расширение базового логгера методами success/notice ===
def patch_logger_with_custom_levels():
    def _make_custom_method(level_name: str, level_num: int):
        def log_method(self, message, *args, **kwargs):
            if self.isEnabledFor(level_num):
                self._log(level_num, message, args, **kwargs)

        return log_method

    for name, num in CUSTOM_LOG_LEVELS.items():
        logging.addLevelName(num, name)
        setattr(logging.Logger, name.lower(), _make_custom_method(name, num))


patch_logger_with_custom_levels()


# === Основной логгер-менеджер ===
class LoggerManager:
    def __init__(
        self,
        name: str = "app",
        debug: bool = False,
        log_dir: Optional[Union[str, Path]] = None,
        log_level: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        self.name = name
        self.debug = debug
        self.log_level = (log_level or "DEBUG" if debug else "INFO").upper()
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        self.log_dir = self._resolve_log_dir(log_dir)
        self.logger = self._setup_logger()

    def _resolve_log_dir(self, log_dir: Optional[Union[str, Path]]) -> Path:
        if log_dir:
            path = Path(log_dir).expanduser()
            try:
                path.mkdir(parents=True, exist_ok=True)
                if os.access(path, os.W_OK):
                    return path
            except Exception as e:
                print(f"⚠️ Невозможно создать каталог логов: {e}", file=sys.stderr)

        # Локальный импорт внутри метода — предотвращает ImportError при циклическом импорте
        try:
            from app.core.patchs import BASE_DIR
        except ImportError:
            BASE_DIR = Path.cwd()

        default_log_dirs = [
            BASE_DIR / "logs",
            Path("/var/log/tgnms"),
            Path("/tmp/tgnms_logs"),
        ]

        for dir_path in default_log_dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                if os.access(dir_path, os.W_OK):
                    return dir_path
            except Exception:
                continue

        fallback = Path.cwd() / "logs"
        fallback.mkdir(parents=True, exist_ok=True)
        print(
            f"⚠️ Все варианты директорий недоступны, логи будут в {fallback}",
            file=sys.stderr,
        )
        return fallback

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level, logging.INFO))
        logger.handlers.clear()

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # === Файловое логирование ===
        if self.enable_file_logging:
            file_handler = RotatingFileHandler(
                self.log_dir / f"{self.name}.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, self.log_level))
            logger.addHandler(file_handler)

        # === Консольное логирование с Rich ===
        if self.enable_console_logging:
            rich_console = Console(theme=RICH_THEME)
            console_handler = RichHandler(
                console=rich_console,
                markup=True,
                rich_tracebacks=self.debug,
                show_path=self.debug,
                tracebacks_show_locals=self.debug,
            )
            console_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
            console_handler.setLevel(getattr(logging, self.log_level))
            logger.addHandler(console_handler)

        return logger

    def get_logger(self) -> logging.Logger:
        return self.logger
