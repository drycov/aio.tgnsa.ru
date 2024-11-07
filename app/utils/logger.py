import sys

from dotenv import load_dotenv
from loguru import logger

from app.constants import LogMessages
from logging_config import LoggingConfig  # Импортируем из нового файла конфигурации

# Загрузка переменных окружения
load_dotenv()


class AppLogger:
    def __init__(self, name="bot_logger", log_level=None, log_format=None, log_file=None):
        # Отложенный импорт Config, чтобы избежать циклического импорта

        log_level = log_level or LoggingConfig.LOGGING_LEVEL
        log_format = log_format or "{time} - {name} - {level} - {message}"
        log_file_path = log_file or (LoggingConfig.LOG_DIR / LoggingConfig.LOG_FILE)

        # Удаление всех стандартных обработчиков loguru
        logger.remove()

        # Настройка логгера для вывода в консоль
        logger.add(
            sys.stdout,
            level=log_level,
            format=log_format
        )

        # Настройка логгера для записи в файл с ежедневной ротацией
        logger.add(
            log_file_path,
            level=log_level,
            format=log_format,
            rotation="00:00",
            retention="14 days",
            encoding="utf-8"
        )

        logger.info(LogMessages.LOGGER_INITIALIZED.value)

    def get_logger(self):
        return logger


# Создание функции для получения логгера вместо создания его сразу
def get_app_logger():
    return AppLogger().get_logger()
