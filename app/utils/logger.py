import logging
import socket
import sys
import json
from logging.handlers import SysLogHandler

from logging_config import LoggingConfig


class AppLogger:
    def __init__(self):
        log_level = LoggingConfig.LOGGING_LEVEL
        log_format = LoggingConfig.LOGGING_FORMAT
        log_file_path = LoggingConfig.LOG_DIR / LoggingConfig.LOG_FILE

        # Параметры для Syslog
        use_syslog = LoggingConfig.USE_SYSLOG
        syslog_host = LoggingConfig.SYSLOG_HOST
        syslog_port = LoggingConfig.SYSLOG_PORT
        syslog_facility = LoggingConfig.SYSLOG_FACILITY
        syslog_message_format = LoggingConfig.SYSLOG_MESSAGE_FORMAT or "{asctime} - {name} - {levelname} - {message}"
        syslog_logging_level = LoggingConfig.SYSLOG_LOGGING_LEVEL

        # Создаем логгер
        self.logger = logging.getLogger("bot_logger")
        self.logger.setLevel(log_level)

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(log_format, style='{')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Обработчик для записи в файл с кодировкой utf-8
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        self.logger.addHandler(file_handler)

        # Настройка syslog, если включено в конфигурации
        if use_syslog:
            self.setup_syslog_handler(
                host=syslog_host,
                port=syslog_port,
                facility=syslog_facility,
                logging_level=syslog_logging_level,
                message_format=syslog_message_format
            )

        self.logger.info("Logger initialized")

    def setup_syslog_handler(self, host, port, facility, logging_level, message_format):
        """Настройка Syslog-обработчика для логгера."""
        syslog_handler = SysLogHandler(
            address=(host, port),
            facility=facility,
            socktype=socket.SOCK_DGRAM
        )

        syslog_handler.setLevel(logging_level)
        syslog_formatter = logging.Formatter(message_format, style='{')
        syslog_handler.setFormatter(syslog_formatter)
        self.logger.addHandler(syslog_handler)
        self.logger.info("Syslog handler initialized.")

    def get_logger(self):
        return self.logger


# Функция для получения экземпляра логгера
def get_app_logger():
    return AppLogger().get_logger()


# Пример использования json.dumps с ensure_ascii=True
def log_json_data(logger, data):
    json_data = json.dumps(data, ensure_ascii=True)
    logger.info(f"Received JSON data: {json_data}")
