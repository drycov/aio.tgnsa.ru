# config.py
import logging
import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv

# Загрузка переменных окружения из .env и config.env
load_dotenv()
basedir = Path(__file__).resolve().parent
config_env_path = basedir / "config.env"
if config_env_path.exists():
    click.secho("Импортирование окружения из файла config.env", fg="cyan")
    with config_env_path.open() as f:
        for line in f:
            var = line.strip().split("=")
            if len(var) == 2:
                os.environ[var[0]] = var[1].replace('"', "")

# Полные пути к директориям
paths = {
    "logs": basedir / "logs",
    "data": basedir / "data",
}

# Создание директорий, если они не существуют
for name, path in paths.items():
    if not path.is_dir():
        click.secho(f"⚠️ Директория {name} не существует. Создаем её...", fg="yellow")
        path.mkdir(parents=True, exist_ok=True)

# Версия Python
PYTHON_VERSION = sys.version_info[0]

class Config:
    """Базовая конфигурация приложения."""

    # ---------- Основные настройки приложения ----------
    APP_NAME = os.getenv("APP_NAME", "TgNSA")
    VERSION = os.getenv("VERSION", "1.0.0")
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@tgnsa.ru")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tgnsa.ru")
    BASE_DIR = basedir
    DATA_PATH = os.getenv("DATA_PATH", basedir / "data")

    # ---------- Локализация и время ----------
    DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "en")
    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")

    # ---------- Параметры бота ----------
    API_TOKEN = os.getenv("API_TOKEN")
    BOT_CHAT_ADMIN_ID = os.getenv("BOT_CHAT_ADMIN_ID")
    BOT_TG_ID = os.getenv("BOT_TG_ID")
    DEFAULT_ADMIN_ID = os.getenv("DEFAULT_ADMIN_ID")

    # ---------- Параметры баз данных ----------
    # Firebase
    DATABASE_URL = os.getenv("DATABASE_URL", "https://ttcnsa-default-rtdb.asia-southeast1.firebasedatabase.app")

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://user:password@cluster.mongodb.net")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ttcNSA")

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
    APP_TYPE = os.getenv("APP_TYPE", "PROD")
    LOGGING_LEVEL = logging.DEBUG if APP_TYPE == "DEV" else logging.INFO
    LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DIR = paths['logs']
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")

    # ---------- Redis и кэширование ----------
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    USE_REDIS = os.getenv("USE_REDIS", "False").lower() == "true"
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")

    # ---------- Настройки электронной почты ----------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-mail.outlook.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # Пример: ttcnsb1@hotmail.com
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
    EXCLUDED_SUBSTRINGS = os.getenv("EXCLUDED_SUBSTRINGS", "Vl,vl,Loop,Lo,null,Nu,me,loop,tunne,oob,stack-port,noSuchInstance").split(",")
