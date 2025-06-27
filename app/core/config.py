import json
import os
import secrets
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from dotenv import load_dotenv, set_key
from pydantic import (
    Field,
    SecretStr,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core import LoggerManager
from app.core.utils.version import __version__

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / "app"
PLUGIN_DIR = APP_DIR / "plugins"
PLUGIN_CONGIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
ENV_PATH = BASE_DIR / ".env"
SUPPORTED_ENGINES = {"sqlite", "postgres", "mysql", "mariadb"}

# --- Load .env early ---
load_dotenv(dotenv_path=ENV_PATH, override=True)

# --- Role setup from env ---
APP_ROLE = os.getenv("APP_ROLE", "app")


class AppSettings(BaseSettings):
    """
    Основные настройки приложения FastBill.

    Attributes:
        APP_NAME (str): Название приложения
        VERSION (str): Версия приложения
        DESCRIPTION (str): Описание приложения
        DEFAULT_TIMEZONE (str): Часовой пояс по умолчанию
        DEFAULT_USER (str): Имя пользователя по умолчанию
        DEFAULT_PASSWORD (str): Пароль по умолчанию
        DEFAULT_EMAIL (str): Email по умолчанию
        DEFAULT_USER_FULLNAME (str): Полное имя пользователя по умолчанию
    """

    APP_NAME: str = "TG NMS"
    DESCRIPTION: str = (
        "**TG NMS** — модульная система управления сетевой инфраструктурой для малых и средних ISP. "
        "Включает мониторинг, автоматизацию расчётов, управление абонентами, интеграцию с платёжными системами "
        "и сетевыми устройствами. Ориентирована на надёжность, простоту и масштабируемость."
    )
    DEFAULT_USER: str = "root"
    DEFAULT_PASSWORD: str = "root"
    DEFAULT_EMAIL: str = "admin@example.com"
    DEFAULT_USER_FULLNAME: str = "Admin"
    FAVICON_PATH: str = "img/logo.png"
    # Настройки статических файлов
    STATIC_URL: str = "/static"
    MEDIA_URL: str = "/media"

    @property
    def app_str(self) -> str:
        """Возвращает строку с информацией о приложении."""
        return f"{self.APP_NAME} v{self.VERSION}"

    @property
    def favicon_url(self) -> str:
        """Возвращает полный URL для favicon."""
        return f"{self.STATIC_URL}/{self.FAVICON_PATH}"

    @property
    def static_url(self) -> str:
        """Возвращает URL для статических файлов."""
        return self.STATIC_URL

    model_config = {
        "env_file": ENV_PATH,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
        "env_prefix": "APP_",
    }


class PostgresConfig(BaseSettings):
    HOST: str = Field(..., env="POSTGRES_HOST")
    PORT: int = Field(5432, env="POSTGRES_PORT")
    USER: str = Field(..., env="POSTGRES_USER")
    PASSWORD: SecretStr = Field(..., env="POSTGRES_PASSWORD")
    NAME: str = Field(..., env="POSTGRES_DB")

    def dsn(self, driver: Optional[str] = None) -> str:
        """
        Генерация строки подключения с учетом выбранного драйвера.

        :param driver: Опционально указывается драйвер SQLAlchemy (например, 'asyncpg', 'psycopg2', 'pg8000').
        :return: Полная строка подключения.
        """
        driver_prefix = f"+{driver}" if driver else ""
        return f"postgresql{driver_prefix}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    model_config = {
        "env_file": ENV_PATH,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
        "env_prefix": "POSTGRES_",
    }


class SqliteConfig(BaseSettings):
    FILE: str = Field("app.db", env="SQLITE_FILE")

    def _resolved_path(self) -> str:  # ✅ должна быть функция
        db_path = self.FILE
        return db_path if os.path.isabs(db_path) else str(DATA_DIR / db_path)

    def dsn(self) -> str:
        return f"sqlite+aiosqlite:///{self._resolved_path()}"

    def async_dsn(self) -> str:
        return f"sqlite+aiosqlite:///{self._resolved_path()}"

    def sync_dsn(self) -> str:
        return f"sqlite:///{self._resolved_path()}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="SQLITE_",
    )


class MySQLConfig(BaseSettings):
    HOST: str = Field(..., env="MYSQL_HOST")
    PORT: int = Field(3306, env="MYSQL_PORT")
    USER: str = Field(..., env="MYSQL_USER")
    PASSWORD: SecretStr = Field(..., env="MYSQL_PASSWORD")
    NAME: str = Field(..., env="MYSQL_DB")

    def dsn(self) -> str:
        return f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="MYSQL_",
    )


class DBSettings(BaseSettings):
    engine: Literal["sqlite", "postgres", "mysql"] = Field(
        default="sqlite", env="DB_ENGINE"
    )
    postgres: Optional[PostgresConfig] = None
    mysql: Optional[MySQLConfig] = None
    sqlite: Optional[SqliteConfig] = None
    echo: bool = Field(default=False, env="DB_ECHO")

    @model_validator(mode="after")
    def load_db_config(cls, values):
        match values.engine:
            case "postgres":
                values.postgres = PostgresConfig()
            case "mysql":
                values.mysql = MySQLConfig()
            case "sqlite":
                values.sqlite = SqliteConfig()
        return values

    def get_db_config(self):
        return {
            "postgres": self.postgres,
            "mysql": self.mysql,
            "sqlite": self.sqlite,
        }.get(self.engine)

    def get_dsn(self) -> str:
        if config := self.get_db_config():
            return config.dsn()
        else:
            raise ValueError(
                f"❌ DB_ENGINE={self.engine} не поддерживается или не сконфигурирован"
            )

    def get_sync_dsn(self) -> str:
        if config := self.get_db_config():
            return config.sync_dsn() if hasattr(config, "sync_dsn") else config.dsn()
        else:
            raise ValueError(
                f"❌ DB_ENGINE={self.engine} не поддерживается или не сконфигурирован"
            )


class BotConfig(BaseSettings):
    TOKEN: SecretStr
    # .env: ADMINS=123456789,987654321
    ADMINS: Set[int] = Field(
        default_factory=set, description="Список ID администраторов", env="ADMINS"
    )

    SUPERUSERS: Set[int] = Field(
        default_factory=set,
        description="Список ID суперпользователей (имеют полный доступ)",
        env="SUPERUSERS",
    )
    RATE_LIMIT: float = Field(
        default=1.0, description="Лимит запросов в секунду", env="RATE_LIMIT"
    )

    ROLE_ACCESS: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Словарь прав доступа для ролей",
        env="ROLE_ACCESS",
    )

    @field_validator("ADMINS", "SUPERUSERS", mode="before")
    @classmethod
    def parse_json_or_csv(cls, v: Any) -> Set[int]:
        if isinstance(v, str):
            v = v.strip()
            try:
                # Пробуем JSON-декодинг
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return {int(i) for i in parsed if str(i).isdigit()}
            except json.JSONDecodeError:
                # Фоллбек: CSV-разбор
                return {int(i.strip()) for i in v.split(",") if i.strip().isdigit()}
        elif isinstance(v, list | set):
            return {int(i) for i in v}
        return set()

    @field_validator("ROLE_ACCESS", mode="before")
    @classmethod
    def parse_role_access(cls, v):
        import json

        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                # Пытаемся распарсить как JSON
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                elif isinstance(parsed, list):
                    # Преобразуем ["admin", "user"] в {"default": [...]}
                    return {"default": parsed}
            except json.JSONDecodeError:
                # CSV fallback: admin,user → {"default": [...]}
                return {
                    "default": [item.strip() for item in v.split(",") if item.strip()]
                }
        elif isinstance(v, list):
            return {"default": v}
        raise ValueError(
            "Неверный формат ROLE_ACCESS — должен быть словарём или списком"
        )

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="BOT_",
    )


class MongoDBConfig(BaseSettings):
    URI: str = Field(default="", env="MONGO_URI")
    DB_NAME: str = Field(default="", env="MONGO_DB_NAME")
    PORT: Optional[int] = Field(default=None, env="MONGO_PORT")
    USER: Optional[str] = Field(default=None, env="MONGO_USER")
    PASSWORD: Optional[SecretStr] = Field(default=None, env="MONGO_PASSWORD")
    USE_SRV: bool = Field(False, env="MONGO_USE_SRV")

    def dsn(self) -> str:
        if self.URI:
            return self.URI  # Используем URI напрямую, если задан

        # Базовая часть: хост и порт
        host = "localhost"
        # port = self.PORT or 27017

        # Аутентификация
        auth = ""
        if self.USER:
            user = self.USER
            password = self.PASSWORD or ""
            auth = f"{user}:{password}@"

        # Имя БД
        db_name = self.DB_NAME or "admin"
        scheme = "mongodb+srv" if self.USE_SRV else "mongodb"
        return f"{scheme}://{auth}{host}/{db_name}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="MONGO_",
        case_sensitive=True,
        extra="ignore",
    )


class RedisConfig(BaseSettings):
    HOST: str = Field("localhost", env="REDIS_HOST")
    PORT: int = Field(6379, env="REDIS_PORT")
    PASSWORD: SecretStr | None = Field(None, env="REDIS_PASSWORD")
    DB: int = Field(0, env="REDIS_DB")
    USE_TLS: bool = Field(False, env="CACHE_REDIS_USE_TLS")

    def dsn(self) -> str:
        scheme = "rediss" if self.USE_TLS else "redis"
        auth = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"{scheme}://{auth}{self.HOST}:{self.PORT}/{self.DB}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        case_sensitive=True,
        extra="ignore",
    )


class CacheRedisConfig(BaseSettings):
    HOST: str = Field("localhost", env="CACHE_REDIS_HOST")
    PORT: int = Field(6379, env="CACHE_REDIS_PORT")
    PASSWORD: Optional[SecretStr] = Field(None, env="CACHE_REDIS_PASSWORD")
    DB: int = Field(1, env="CACHE_REDIS_DB")
    USE_TLS: bool = Field(False, env="CACHE_REDIS_USE_TLS")

    def dsn(self) -> str:
        scheme = "rediss" if self.USE_TLS else "redis"
        auth = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"{scheme}://{auth}{self.HOST}:{self.PORT}/{self.DB}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="CACHE_REDIS_",
        case_sensitive=True,
        extra="ignore",
    )


class TFAConfig(BaseSettings):
    ENABLE: bool = Field(default=False, env="TFA_ENABLE")
    MANDATORY: list[int] = Field(default_factory=list, env="TFA_MANDATORY")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_prefix="TFA_", case_sensitive=True, extra="ignore"
    )


class Security(BaseSettings):
    TFA_ENABLE: bool = Field(default=False, env="TFA_ENABLE")

    JWT_SECRET: SecretStr | None = Field(default=None, env="SECURITY_JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", env="SECURITY_JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60, env="SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ACCESS_TOKEN_EXPIRE_SECONDS: int = Field(
        3600, env="SECURITY_ACCESS_TOKEN_EXPIRE_SECONDS"
    )

    ADMIN_PASSWORD: SecretStr | None = Field(
        default=None, env="SECURITY_ADMIN_PASSWORD"
    )
    USE_SPECIAL_CHAR: bool = Field(default=False, env="SECURITY_USE_SPECIAL_CHAR")
    MIN_LENGTH: int = Field(default=8, env="SECURITY_MIN_LENGTH")
    tfa: Optional[TFAConfig] = None

    @model_validator(mode="after")
    def conditional_tfa_load(cls, values):
        values.tfa = TFAConfig() if values.TFA_ENABLE else None
        return values

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="SECURITY_",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def generate_and_save_missing_secrets(cls, values):
        from .password import generate_password  # новый путь

        updated = False

        def save_secret_to_env(key: str, secret_value: str):
            # Записываем ключ в .env
            set_key(str(ENV_PATH), key, secret_value)

        if values.JWT_SECRET is None or (
            isinstance(values.JWT_SECRET, str) and not values.JWT_SECRET
        ):
            new_secret = secrets.token_urlsafe(32)
            values.JWT_SECRET = SecretStr(new_secret)
            save_secret_to_env("SECURITY_JWT_SECRET", new_secret)
            updated = True

        if values.ADMIN_PASSWORD is None or (
            isinstance(values.ADMIN_PASSWORD, str) and not values.ADMIN_PASSWORD
        ):
            password = generate_password(length=8, use_special=False)
            values.ADMIN_PASSWORD = SecretStr(password)
            save_secret_to_env("SECURITY_ADMIN_PASSWORD", password)
            updated = True

        if updated:
            print(f"⚡ Сгенерированы новые секреты и записаны в {ENV_PATH}")

        return values


class MiddlewareConfig(BaseSettings):
    """Конфигурация middleware для бота

    Attributes:
        rate_limit: Лимит запросов в секунду
        admins: Список ID администраторов
        superusers: Список ID суперпользователей (имеют полный доступ)
        role_access: Словарь прав доступа для ролей
        enable_profiler: Включить профилирование
        enable_tfa: Включить двухфакторную аутентификацию
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="BOT_",
    )

    # Настройки ограничений
    rate_limit: float = Field(
        default=1.0, description="Лимит запросов в секунду", env="RATE_LIMIT"
    )

    # Настройки доступа

    # Настройки ограничений
    rate_limit: float = Field(
        default=1.0, description="Лимит запросов в секунду", env="RATE_LIMIT"
    )

    role_access: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Словарь прав доступа для ролей",
        env="ROLE_ACCESS",
    )

    # Флаги функциональности
    enable_profiler: bool = Field(
        default=False,
        description="Включить профилирование производительности",
        env="ENABLE_PROFILER",
    )

    def is_superuser(self, user_id: str) -> bool:
        """Проверяет, является ли пользователь суперпользователем"""
        return user_id in self.superusers

    def is_admin(self, user_id: str) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in self.admins or self.is_superuser(user_id)


class NetworkConfig(BaseSettings):
    PING_COUNT: int = Field(default=4, env="NETWORK_PING_COUNT")
    PING_INTERVAL: int = Field(default=2, env="NETWORK_PING_INTERVAL")
    PING_TIMEOUT: int = Field(default=10, env="NETWORK_PING_TIMEOUT")
    SNMP_RO: list[str] = Field(default_factory=list, env="NETWORK_SNMP_RO")
    SNMP_RW: list[str] = Field(default_factory=list, env="NETWORK_SNMP_RW")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_prefix="NETWORK_", case_sensitive=True, extra="ignore"
    )


class CacheConfig(BaseSettings):
    CACHE_TYPE: Literal["SimpleCache", "RedisCache", "None"] = Field(
        default="None", env="CACHE_TYPE"
    )
    redis: Optional[CacheRedisConfig] = None

    @model_validator(mode="after")
    def load_cache_config(cls, values: "CacheConfig"):
        if values.CACHE_TYPE == "RedisCache":
            values.redis = CacheRedisConfig()
        return values

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


class MiscConfig(BaseSettings):
    TIMEZONE: str = Field(default="UTC", env="TIMEZONE")
    MAX_PAYLOAD_SIZE_MB: int = Field(default=10, env="MAX_PAYLOAD_SIZE_MB")
    EXCLUDED_SUBSTRINGS: Optional[str] = Field(default="", env="EXCLUDED_SUBSTRINGS")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH, case_sensitive=True, extra="ignore"
    )


class EmailConfig(BaseSettings):
    SMTP_HOST: str = Field(..., env="EMAIL_SMTP_HOST")
    SMTP_PORT: int = Field(..., env="EMAIL_SMTP_PORT")
    SMTP_USER: str = Field(..., env="EMAIL_SMTP_USER")
    SMTP_PASSWORD: SecretStr = Field(..., env="EMAIL_SMTP_PASSWORD")
    FROM_EMAIL: Optional[str] = Field(default=None, env="EMAIL_FROM")
    ENABLE_TLS: bool = Field(default=True, env="EMAIL_ENABLE_TLS")
    SUPPORT_EMAIL: Optional[str] = Field(default=None, env="EMAIL_SUPPORT_EMAIL")
    ADMIN_EMAIL: Optional[str] = Field(default=None, env="EMAIL_ADMIN_EMAIL")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="EMAIL_",
        case_sensitive=True,
        extra="ignore",
    )


class ApiServerConfig(BaseSettings):
    API_HOST: str = Field(default="127.0.0.1", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=1, env="API_WORKERS")
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix=" API_",
        case_sensitive=True,
        extra="ignore",
    )


class Settings(BaseSettings):
    USE_REDIS: bool = Field(default=False, env="USE_REDIS")
    USE_FS: bool = Field(default=False, env="USE_FS")
    USE_MONGODB: bool = Field(default=False, env="USE_MONGODB")
    USE_FIREBASE: bool = Field(default=False, env="USE_FIREBASE")
    USE_CACHE: bool = Field(default=False, env="USE_CACHE")
    DEBUG: bool = Field(default=False, env="DEBUG")

    bot: BotConfig = Field(default_factory=BotConfig)
    db: DBSettings = Field(default_factory=DBSettings)
    redis: Optional[RedisConfig] = None
    security: Security = Field(default_factory=Security)
    mongo: Optional[MongoDBConfig] = None
    net: NetworkConfig = Field(default_factory=NetworkConfig)
    cache: Optional[CacheConfig] = None
    misc: MiscConfig = Field(default_factory=MiscConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    api: ApiServerConfig = Field(default_factory=ApiServerConfig)
    app: AppSettings = Field(default_factory=AppSettings)

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def conditional_redis_load(cls, values):
        values.redis = RedisConfig() if values.USE_REDIS else None
        return values

    @model_validator(mode="after")
    def conditional_nongo_load(cls, values):
        values.mongo = MongoDBConfig() if values.USE_MONGODB else None
        return values

    @model_validator(mode="after")
    def conditional_cache_load(cls, values):
        values.cache = CacheConfig() if values.USE_CACHE else None
        return values

    @model_validator(mode="before")
    def validate_db_engine(cls, values):
        engine = values.get("DB_ENGINE")
        if not engine and "db" in values:
            db = values["db"]
            if isinstance(db, DBSettings):
                engine = db.engine
            elif isinstance(db, dict):
                engine = db.get("engine")
        if engine not in SUPPORTED_ENGINES:
            raise ValueError(f"❌ DB_ENGINE={engine} не поддерживается.")
        return values

    @computed_field
    @property
    def VERSION(self) -> str:
        return __version__


# --- Settings init ---
settings = Settings()

# --- Debug mode resolution ---


def resolve_debug_mode() -> bool:
    try:
        return bool(settings.DEBUG)
    except Exception:
        return os.getenv("DEBUG", "").lower() in ("1", "true", "yes")


debug_mode = resolve_debug_mode()

# --- Logger Initialization ---
logger = LoggerManager(name=APP_ROLE, debug=debug_mode).get_logger()
