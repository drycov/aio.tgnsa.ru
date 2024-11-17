import os
from pathlib import Path

import click
from dotenv import load_dotenv

# Определение базовой директории и конфигурационного файла
basedir = Path(__file__).resolve().parent
config_env_path = basedir / ".env"

# Загрузка переменных окружения из .env и .env (если он существует)
load_dotenv()  # Загрузка из .env

if config_env_path.exists():
    click.secho("Импортирование окружения из файла .env", fg="green")
    load_dotenv(dotenv_path=config_env_path, override=True)  # Переопределение переменных из .env


class LoggingConfig:
    # Настройки логирования из переменных окружения
    APP_TYPE = os.getenv("APP_TYPE", "PROD")
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
    LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "{asctime} - {name} - {levelname} - {message}")

    # Директория для логов
    LOG_DIR = Path(os.getenv("LOG_DIR", basedir / "logs")).resolve()

    # Настройки Syslog
    USE_SYSLOG = os.getenv("USE_SYSLOG", "True").lower() in ["true", "1"]
    SYSLOG_HOST = os.getenv("SYSLOG_HOST", "127.0.0.1")
    SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", 514))
    SYSLOG_FACILITY = os.getenv("SYSLOG_FACILITY", "local7")
    SYSLOG_MESSAGE_FORMAT = os.getenv("SYSLOG_MESSAGE_FORMAT", "{asctime} - {name} - {levelname} - {message}")
    SYSLOG_LOGGING_LEVEL = os.getenv("SYSLOG_LOGGING_LEVEL", "WARNING")

    @classmethod
    def ensure_log_dir_exists(cls):
        """Создание директории логов, если не существует."""
        if not cls.LOG_DIR.exists():
            cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
            click.secho(f"Директория для логов создана: {cls.LOG_DIR}", fg="yellow")


# Убедитесь, что директория логов существует
LoggingConfig.ensure_log_dir_exists()
