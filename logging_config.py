import os
from pathlib import Path

from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение базовой директории
basedir = Path(__file__).resolve().parent


class LoggingConfig:
    APP_TYPE = os.getenv("APP_TYPE", "PROD")
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
    LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "{time} - {name} - {level} - {message}")

    # Используем переменную окружения для пути к логам
    LOG_DIR = Path(os.getenv("LOG_DIR", basedir / "logs")).resolve()

    @staticmethod
    def ensure_log_dir_exists():
        # Убедитесь, что директория для логов существует
        if not LoggingConfig.LOG_DIR.exists():
            LoggingConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Директория для логов создана: {LoggingConfig.LOG_DIR}")


# Убедитесь, что директория логов создана
LoggingConfig.ensure_log_dir_exists()
