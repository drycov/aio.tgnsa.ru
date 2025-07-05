# app/core/logging_setup.py

import logging
from app.core.utils.logger_manager import LoggerManager
from app.core.config import APP_ROLE, debug_mode


def configure_logger(name: str = None) -> logging.Logger:
    """
    Конфигурирует и возвращает настроенный логгер.

    :param name: Имя логгера (по умолчанию из APP_ROLE)
    :return: Настраиваемый логгер
    """
    logger_name = name or APP_ROLE
    return LoggerManager(name=logger_name, debug=debug_mode).get_logger()


# Глобальный логгер по умолчанию
logger = configure_logger()