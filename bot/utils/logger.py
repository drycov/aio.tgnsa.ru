import inspect
import json
import logging
import socket
import sys
from logging.handlers import SysLogHandler
from pathlib import Path
from typing import Any, Dict, Optional

from logging_config import LoggingConfig


class AppLogger:
    def __init__(self, name: Optional[str] = None) -> None:
        """
        Инициализирует логгер с именем вызывающего модуля.
        :param name: Имя логгера. Если не указано, используется имя модуля, вызвавшего этот класс.
        """
        self.name = name or inspect.stack()[1].frame.f_globals["__name__"]
        self.logger = logging.getLogger(self.name)
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Настраивает логгер с обработчиками для консоли, файла и Syslog."""
        self.logger.setLevel(LoggingConfig.LOGGING_LEVEL)

        # Общий форматтер для всех обработчиков
        formatter = logging.Formatter(LoggingConfig.LOGGING_FORMAT, style="{")

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Обработчик для записи в файл
        log_file_path = LoggingConfig.LOG_DIR / LoggingConfig.LOG_FILE
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Обработчик для Syslog, если включен
        if LoggingConfig.USE_SYSLOG:
            self._setup_syslog_handler()

        self.logger.info(f"Logger initialized in module: {self.name}")

    def _setup_syslog_handler(self) -> None:
        """Настраивает Syslog-обработчик для логгера."""
        syslog_handler = SysLogHandler(
            address=(LoggingConfig.SYSLOG_HOST, LoggingConfig.SYSLOG_PORT),
            facility=LoggingConfig.SYSLOG_FACILITY,
            socktype=socket.SOCK_DGRAM,
        )
        syslog_formatter = logging.Formatter(
            LoggingConfig.SYSLOG_MESSAGE_FORMAT or "{asctime} - {name} - {levelname} - {message}",
            style="{",
        )
        syslog_handler.setFormatter(syslog_formatter)
        syslog_handler.setLevel(LoggingConfig.SYSLOG_LOGGING_LEVEL)
        self.logger.addHandler(syslog_handler)
        self.logger.info("Syslog handler initialized.")

    def get_logger(self) -> logging.Logger:
        """Возвращает настроенный логгер."""
        return self.logger


def get_app_logger() -> logging.Logger:
    """
    Возвращает экземпляр логгера, автоматически определяя имя вызывающего модуля.
    :return: Настроенный логгер.
    """
    return AppLogger().get_logger()


def log_json_data(logger: logging.Logger, data: Dict[str, Any]) -> None:
    """
    Логирует данные в формате JSON.
    :param logger: Логгер для записи сообщений.
    :param data: Данные для логирования.
    """
    json_data = json.dumps(data, ensure_ascii=True)
    logger.info(f"Received JSON data: {json_data}")