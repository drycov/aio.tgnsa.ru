# logger.py
import logging
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv

from app.constants import LogMessages
from config import Config

# Загрузка переменных окружения
load_dotenv()

# Формат логирования
formatter = logging.Formatter(Config.LOGGING_FORMAT)

# Создание логгера
logger = logging.getLogger("bot_logger")
logger.setLevel(Config.LOGGING_LEVEL)

# Обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Обработчик для записи в файл с ежедневной ротацией
log_file_path = Config.LOG_DIR / Config.LOG_FILE
file_handler = TimedRotatingFileHandler(
    filename=log_file_path,
    when="midnight",  # Ротация каждый день в полночь
    interval=1,  # Интервал ротации — 1 день
    backupCount=14,  # Максимальное количество файлов
    encoding="utf-8",  # Кодировка для файлов лога
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)  # Запись только сообщений уровня INFO и выше
logger.addHandler(file_handler)

# Сообщение при запуске логгера
logger.info(LogMessages.LOGGER_INITIALIZED)
