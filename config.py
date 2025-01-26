# config.py
import os
import sys
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Получение экземпляра логгера

# Загрузка переменных окружения из .env и .env
load_dotenv()
basedir = Path(__file__).resolve().parent
config_env_path = basedir / ".env"
# Проверка существования файла и импортирование переменных окружения
if config_env_path.exists():
    logger.info("Импортирование окружения из файла .env")
    with config_env_path.open() as f:
        for line in f:
            # Убираем пробельные символы и игнорируем пустые строки или комментарии
            line = line.strip()
            if line and not line.startswith("#"):
                var = line.split("=")
                if len(var) == 2:
                    key, value = var
                    # Убираем возможные кавычки вокруг значений
                    os.environ[key] = value.replace('"', '').replace("'", "")
                else:
                    logger.warning(f"Некорректная строка в .env: {line}")
else:
    logger.error(f"Файл {config_env_path} не существует.")

# Полные пути к директориям
paths = {
    "logs": basedir / "logs",
    "data": basedir / "data",
}

# Создание директорий, если они не существуют
for name, path in paths.items():
    if not path.is_dir():
        logger.info(f"⚠️ Директория {name} не существует. Создаем её...")
        path.mkdir(parents=True, exist_ok=True)

# Версия Python
PYTHON_VERSION = sys.version_info[0]


class Config:
    """Базовая конфигурация приложения."""

    # ---------- Основные настройки приложения ----------
    APP_NAME = os.getenv("APP_NAME", "TgNSA")
    VERSION = os.getenv("VERSION", "0.1.0")
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@tgnsa.ru")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tgnsa.ru")
    BASE_DIR = basedir
    DATA_PATH = os.getenv("DATA_PATH", basedir / "data")
    DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1"]
    SECRET_KEY = os.getenv("SECRET_KEY")
    GATEWAY_IP = os.getenv("GATEWAY_IP")

    # ---------- Настройки бота ----------
    license = "MIT"  # Например, укажите нужную лицензию
    vendor_info = {
        "botVendor": "Denis Rykov",
        "botVendorTGContact": "@ITISIDevRykov",
        "botVendorContact": "https://t.me/ITISIDevRykov",
        "botVendorEMailContact": "d.rykov@ttc.kz",
        "botVendorWContact": "+7-771-051-5252"
    }
    # ---------- Локализация и время ----------
    DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "ru_RU.UTF-8")
    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")

    # ---------- Параметры бота ----------
    API_TOKEN = os.getenv("API_TOKEN")
    BOT_CHAT_ADMIN_ID = os.getenv("BOT_CHAT_ADMIN_ID")
    BOT_TG_ID = os.getenv("BOT_TG_ID")
    DEFAULT_ADMIN_ID = os.getenv("DEFAULT_ADMIN_ID")

    # ---------- Параметры баз данных ----------
    # Firebase
    FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL ",
                                      "https://ttcnsa-default-rtdb.asia-southeast1.firebasedatabase.app")

    # MongoDB
    USE_MONGODB = os.getenv("USE_MONGODB", "False").lower() in ("true", "1", "yes", "True")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "fsm-aio")

    # SQLite (локальная база данных)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{paths['data'] / 'app.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    SQLALCHEMY_RECORD_QUERIES = os.getenv("SQLALCHEMY_RECORD_QUERIES", "False").lower() == "true"
    SQLALCHEMY_SLOW_QUERY_THRESHOLD = int(os.getenv("SQLALCHEMY_SLOW_QUERY_THRESHOLD", 1))

    # ---------- Настройки Ping для устройств ----------
    PING_COUNT = int(os.getenv("PING_COUNT", 4))
    PING_INTERVAL = int(os.getenv("PING_INTERVAL", 2))
    PING_TIMEOUT = int(os.getenv("PING_TIMEOUT", 10))

    # ---------- Логирование ----------

    # ---------- Redis и кэширование ----------
    REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/")
    USE_REDIS = os.getenv("USE_REDIS", "False").lower() in ("true", "1", "yes", "True")
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    # Парсинг REDIS_URL для настройки переменных конфигурации RQ
    if PYTHON_VERSION == 3:
        urllib.parse.uses_netloc.append("redis")
        url = urllib.parse.urlparse(REDIS_URL)

        REDIS_HOST = url.hostname
        REDIS_PORT = url.port
        RQ_DEFAULT_HOST = url.hostname
        RQ_DEFAULT_PORT = url.port
        RQ_DEFAULT_PASSWORD = url.password
        RQ_DEFAULT_DB = 0

    # ---------- Настройки электронной почты ----------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-mail.outlook.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", ADMIN_EMAIL)  # Пример: ttcnsb1@hotmail.com
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # Пример: OSKQAZwsx2022*
    EMAIL_SUBJECT_PREFIX = f"[{APP_NAME}]"
    EMAIL_SENDER = f"{APP_NAME} Admin <{MAIL_USERNAME}>"

    # ---------- Параметры SNMP ----------
    SNMP_COMMUNITIES = os.getenv("SNMP_COMMUNITIES", "public,atbu+1,chinaPublic").split(",")
    SNMP_RW_COMMUNITIES = os.getenv("SNMP_RW_COMMUNITIES", "private").split(",")

    # ---------- Параметры массовых уведомлений ----------
    MASS_INCIDENT_EMAIL = os.getenv("MASS_INCIDENT_EMAIL", "d.rykov@ttc.kz")
    MASS_INCIDENT_SUBJECT = os.getenv("MASS_INCIDENT_SUBJECT", "Массовый инцидент")

    # ---------- Контактные данные вендора ----------
    VENDOR_NAME = os.getenv("VENDOR_NAME", "Denis Rykov")
    VENDOR_CONTACT_USERNAME = os.getenv("VENDOR_CONTACT_USERNAME", "@Oritorius")
    VENDOR_EMAIL = os.getenv("VENDOR_EMAIL", "d.rykov@ttc.kz")
    VENDOR_PHONE = os.getenv("VENDOR_PHONE", "+7-771-051-5252")

    # ---------- Списки исключений ----------
    EXCLUDED_SUBSTRINGS = os.getenv("EXCLUDED_SUBSTRINGS",
                                    "Vl,VLAN,vl,Loop,Lo,null,Nu,me,loop,tunne,oob,stack-port,noSuchInstance").split(",")

    # ---------- Настройки Housekeeper ----------
    # Указатель на контейнерное окружение

    IS_CONTAINER = os.path.exists('/.dockerenv') or os.getenv("HOUSEKEEPER_CONTAINER_MODE", "False").lower() == "true"

    HOUSEKEEPER_ENABLED = os.getenv("HOUSEKEEPER_ENABLED", "False").lower() == "true"
    HOUSEKEEPER_INTERVAL = int(os.getenv("HOUSEKEEPER_INTERVAL", 3600))
    HOUSEKEEPER_DAYS_THRESHOLD = int(os.getenv("HOUSEKEEPER_DAYS_THRESHOLD", 15))
    HOUSEKEEPER_INACTIVITY_THRESHOLD = int(os.getenv("HOUSEKEEPER_INACTIVITY_THRESHOLD", 86400))
    HOUSEKEEPER_MAX_THREADS = int(os.getenv("HOUSEKEEPER_MAX_THREADS", 10))
    HOUSEKEEPER_MAX_REQUESTS = int(os.getenv("HOUSEKEEPER_MAX_REQUESTS", 1000))
    HOUSEKEEPER_MAX_CONCURRENT_REQUESTS = int(os.getenv("HOUSEKEEPER_MAX_CONCURRENT_REQUESTS", 50))
    HOUSEKEEPER_MAX_RETRY_ATTEMPTS = int(os.getenv("HOUSEKEEPER_MAX_RETRY_ATTEMPTS", 3))
    HOUSEKEEPER_MAX_RETRY_DELAY = int(os.getenv("HOUSEKEEPER_MAX_RETRY_DELAY", 300))
    HOUSEKEEPER_RETRY_DELAY_MULTIPLIER = int(os.getenv("HOUSEKEEPER_RETRY_DELAY_MULTIPLIER", 2))
    HOUSEKEEPER_MAX_QUEUE_SIZE = int(os.getenv("HOUSEKEEPER_MAX_QUEUE_SIZE", 10000))
    HOUSEKEEPER_QUEUE_NAME = os.getenv("HOUSEKEEPER_QUEUE_NAME", "default")
    HOUSEKEEPER_TASK_NAME = os.getenv("HOUSEKEEPER_TASK_NAME", "housekeeper")
    HOUSEKEEPER_TASK_CLASS = "housekeeper.tasks.HousekeeperTask"

    # ---------- Настройки дискового пространства ----------
    HEALTHY_CHECK_ENABLE = os.getenv("HEALTHY_CHECK_ENABLE", "False").lower() == "true"
    DISK_SPACE_THRESHOLD_GB = int(os.getenv("DISK_SPACE_THRESHOLD_GB", 2))  # Порог свободного места на диске в ГБ
    RAM_USAGE_THRESHOLD_PERCENT = int(
        os.getenv("RAM_USAGE_THRESHOLD_PERCENT", 80))  # Порог использования RAM в процентах
    HEALTHY_CHECK_INTERVAL = int(os.getenv("HEALTHY_CHECK_INTERVAL", 300))  # Интервал проверок в секундах

    class Security:
        """Настройки безопасности."""
        EXCLUDE_PATHS = ["/login", "/docs", "/openapi.json", "/api/ping"]  # Пути, которые не требуют авторизации
        ALGORITHM = "HS256"

        # Настройки токенов
        class Tokens:
            ACCESS_TOKEN_EXPIRATION = os.getenv("ACCESS_TOKEN_EXPIRATION", "15m")  # Время жизни короткоживущего токена
            REFRESH_TOKEN_EXPIRATION = os.getenv("REFRESH_TOKEN_EXPIRATION", "30d")  # Время жизни refresh-токена
            LONG_LIVED_TOKEN_EXPIRATION = os.getenv("LONG_LIVED_TOKEN_EXPIRATION", "90d")  # Долгоживущий токен
            REVOKE_ON_COMPROMISE = bool(os.getenv("REVOKE_ON_COMPROMISE", True))  # Отзыв токенов при компрометации

        # Настройки паролей
        class Passwords:
            STANDARD_USER_EXPIRATION = os.getenv("STANDARD_USER_EXPIRATION",
                                                 "90d")  # Срок смены для обычных пользователей
            PRIVILEGED_USER_EXPIRATION = os.getenv("PRIVILEGED_USER_EXPIRATION",
                                                   "45d")  # Привилегированные пользователи
            MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", 12))  # Минимальная длина
            REQUIRE_UPPER_CASE = bool(os.getenv("PASSWORD_REQUIRE_UPPER_CASE", True))  # Требовать заглавные буквы
            REQUIRE_LOWER_CASE = bool(os.getenv("PASSWORD_REQUIRE_LOWER_CASE", True))  # Требовать строчные буквы
            REQUIRE_NUMBERS = bool(os.getenv("PASSWORD_REQUIRE_NUMBERS", True))  # Требовать цифры
            REQUIRE_SPECIAL_CHARS = bool(os.getenv("PASSWORD_REQUIRE_SPECIAL_CHARS", True))  # Требовать спецсимволы
            HISTORY_LIMIT = int(os.getenv("PASSWORD_HISTORY_LIMIT", 5))  # Ограничение на повторное использование

        # Настройки двухфакторной аутентификации
        class TwoFactorAuth:
            ENABLED = bool(os.getenv("TFA_ENABLED", True))  # Включить 2FA
            MANDATORY_FOR_ROLES = os.getenv("TFA_MANDATORY_FOR_ROLES", "admin,manager").split(
                ",")  # Роли для обязательного 2FA
        # ---------- Настройки логирования ----------

    class SecurityLogging:
        """Настройки логирования."""
        TOKEN_ACTIVITY = bool(os.getenv("LOG_TOKEN_ACTIVITY", True))  # Логирование активности токенов
        FAILED_LOGINS = bool(os.getenv("LOG_FAILED_LOGINS", True))  # Логирование неудачных попыток входа
        PASSWORD_CHANGES = bool(os.getenv("LOG_PASSWORD_CHANGES", True))  # Логирование смен паролей
