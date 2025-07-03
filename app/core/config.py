import json
import os
from pathlib import Path
import secrets
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from dotenv import load_dotenv
from pydantic import Field, SecretStr, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

from app.core import LoggerManager
from app.core.utils.version import __version__
import tomllib
from loguru import logger as loguru_logger

# --- Путь к проекту ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / "app"
PLUGIN_DIR = APP_DIR / "plugins"
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "config.toml"

SECRETS_TOML = CONFIG_DIR / "secrets.toml"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Файл конфигурации не найден: {CONFIG_PATH}")
DATA_DIR = BASE_DIR / "data"
ENV_PATH = CONFIG_DIR / ".env"
SUPPORTED_ENGINES = {"sqlite", "postgres", "mysql", "mariadb"}
SECRETS_DIR = DATA_DIR / "secrets"
if not SECRETS_DIR.exists():
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)


def load_toml(name: str) -> dict:
    try:
        assert name.exists(), f"{name=} не существует"
        with open(name, "rb") as f:
            return tomllib.load(f)  # выбросит ошибку, если формат неверен
    except FileNotFoundError:
        return {}


SECRETS_DICT = load_toml(SECRETS_TOML)

# --- Загрузка .env заранее ---
load_dotenv(dotenv_path=ENV_PATH, override=True)

# --- Определение роли ---
APP_ROLE = os.getenv("APP_ROLE", "app")


class AppSettings(BaseSettings):
    """Настройки приложения. Содержит имя и версию приложения и все параметры из config.toml."""

    name: str = Field(default=APP_ROLE, description="Имя приложения")
    description: str = Field(
        default="AIO TGNSA - Telegram Network Service Application",
        description="Описание приложения",
    )
    FAVICON_PATH: str = "img/logo.png"
    # Настройки статических файлов
    STATIC_URL: str = "/static"
    MEDIA_URL: str = "/media"
    # Дополнительные параметры по умолчанию (совместимость с config.toml)
    default: dict = Field(default_factory=dict)

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

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="allow",
        secrets_dir=DATA_DIR / "secrets",
    )


class DbEngineSettings(BaseSettings):
    engine: str = Field(..., description="Тип СУБД")
    name: str | None = None
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    echo: bool = False  # поддержка echo из [db]

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="allow",
        secrets_dir=str(DATA_DIR / "secrets"),
    )


class DataBaseSettings(BaseSettings):
    """
    Настройки базы данных.
    - Секция [db] определяет engine
    - Секция [sqlite], [postgres], [mysql] — параметры соответствующего движка
    """

    engine: str = Field(..., description="Тип СУБД")
    name: str | None = None
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    echo: bool = False

    sqlite: dict | None = None
    postgres: dict | None = None
    mysql: dict | None = None
    mariadb: dict | None = None

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="ignore",
        secrets_dir=str(DATA_DIR / "secrets"),
    )

    @model_validator(mode="before")
    def assemble_db(cls, values: dict) -> dict:
        engine = (values.get("engine") or "").strip().lower()
        if engine not in SUPPORTED_ENGINES:
            raise ValueError(f"DB engine '{engine}' не поддерживается")
        # Получаем параметры из одноимённой секции
        engine_config: dict = values.get(engine, {}) or {}
        for key, val in engine_config.items():
            if key not in values or values[key] is None:
                values[key] = val
        # Удаляем старые секции
        for key in ["sqlite", "postgres", "mysql", "mariadb"]:
            if key in values:
                del values[key]
        return values

    def get_sync_dsn(self) -> str:
        """
        Получить DSN для синхронного подключения к базе данных.
        """
        engine = self.engine.lower()

        if engine == "sqlite":
            db_name = self.name or "db.sqlite"
            return f"sqlite:///{DATA_DIR}/{db_name}"

        elif engine == "postgres":
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

        elif engine in {"mysql", "mariadb"}:
            return f"{engine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

        else:
            raise ValueError(f"Неизвестный движок базы данных: {engine}")

    def get_dsn(self) -> str:
        """
        Получить DSN для асинхронного подключения к базе данных.
        """
        engine = self.engine.lower()

        if engine == "sqlite":
            db_name = self.name or "db.sqlite"
            return f"sqlite+aiosqlite:///{DATA_DIR}/{db_name}"

        elif engine == "postgres":
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

        elif engine in {"mysql", "mariadb"}:
            return f"{engine}+aiomysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

        else:
            raise ValueError(f"Неизвестный движок базы данных: {engine}")

class TFAConfig(BaseSettings):
    enabled: bool = Field(default=False, description="Включить TFA")
    issuer: str = Field(default="TG NMS", description="Issuer для TOTP")
    digits: int = Field(default=6, description="Количество цифр в коде")
    period: int = Field(default=30, description="Период действия кода (сек)")
    secret: Optional[SecretStr] = Field(default=None, description="Секрет для генерации TOTP")

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="ignore",
        secrets_dir=str(DATA_DIR / "secrets"),
    )

class Security(BaseSettings):
    """
    Настройки безопасности приложения.
    Используется для хранения секретов и токенов.
    """

    jwt_secret: SecretStr = Field(..., description="Секретный ключ для JWT")

    jwt_algorithm: str = Field(
        default="HS256",
        description="Алгоритм подписи JWT токенов",
    )
    tfa_enable: bool = Field(
        default=False,
        description="Включить двухфакторную аутентификацию (TFA) для всего приложения",
    )

    tfa: Optional[TFAConfig] = None

    @computed_field
    def TFA_ENABLE(self) -> bool:
        """Свойство для получения статуса TFA."""
        return self.tfa_enable

    @model_validator(mode="after")
    def init_jwt_secret_after(self):
        """
        Инициализация или генерация секретного ключа для JWT.
        1️⃣ Проверка наличия в окружении или .env
        2️⃣ Проверка в secrets.toml
        3️⃣ Генерация нового, если не найдено
        """
        raw = getattr(self, "jwt_secret", None) or getattr(self, "JWT_SECRET", None)
        if raw:
            self.jwt_secret = SecretStr(str(raw))
            return self
        # Проверка в secrets.toml
        sec = SECRETS_DICT.get("jwt", {}).get("secret")
        if sec:
            self.jwt_secret = SecretStr(sec)
            return self
        # Генерация нового секрета
        self.jwt_secret = SecretStr(secrets.token_hex(64))
        return self

    @model_validator(mode="after")
    def conditional_tfa_load(self):
        self.tfa = TFAConfig() if self.tfa_enable else None
        return self



    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="ignore",
        toml_file=str(CONFIG_PATH),
        secrets_dir=str(SECRETS_DIR),
    )

    @model_validator(mode="before")
    def init_jwt_secret_before(cls, values: dict) -> dict:
        # 1️⃣ Env/.env/secret_dir (.env overrides secrets_dir)
        raw = values.get("jwt_secret") or values.get("JWT_SECRET")
        if raw:
            values["jwt_secret"] = raw
            return values
        # 2️⃣ secrets.toml (🔐)
        sec = SECRETS_DICT.get("jwt", {}).get("secret")
        if sec:
            values["jwt_secret"] = sec
            return values
        # 3️⃣ генерируем новый
        values["jwt_secret"] = secrets.token_hex(64)
        return values

    @model_validator(mode="before")
    def set_or_generate_secret(cls, values: dict) -> dict:
        # Чтение значения, приоритет TOML → .env → ENV
        raw = values.get("jwt_secret") or values.get("JWT_SECRET")
        if not raw:
            # Генерируем криптографически стойкий секрет ≥512 бит
            generated = secrets.token_hex(64)
            values["jwt_secret"] = generated
        return values


class APISettings(BaseSettings):
    """
    Настройки API приложения.
    Используется для хранения параметров API, таких как хост, порт и количество воркеров.
    """

    api_host: str = Field(default="", description="Хост API сервера")
    api_port: int = Field(default=8000, description="Порт API сервера")
    api_workers: int = Field(
        default=1,
        description="Количество воркеров для API сервера",
    )

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="ignore",
        secrets_dir=DATA_DIR / "secrets",
    )


class BotConfig(BaseSettings):
    token: str | SecretStr = Field(
        default=None,
        description="Токен бота Telegram",)
    # .env: ADMINS=123456789,987654321
    admins: Set[int] = Field(
        default_factory=set, description="Список ID администраторов", env="ADMINS"
    )

    superusers: Set[int] = Field(
        default_factory=set,
        description="Список ID суперпользователей (имеют полный доступ)",
        env="SUPERUSERS",
    )
    rate_limit: float = Field(
        default=1.0, description="Лимит запросов в секунду", env="RATE_LIMIT"
    )

    role_access: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Словарь прав доступа для ролей",
        env="ROLE_ACCESS",
    )

    @field_validator("token", mode="before")
    @classmethod
    def ensure_secretstr(cls, v):
        if v is None or v == "":
            # Динамическая подгрузка из secrets.toml
            from app.core.config import SECRETS_DICT
            token = SECRETS_DICT.get("bot", {}).get("token")
            loguru_logger.debug(f"Проверка токена бота... {token}")
            if not token:
                raise ValueError("Token не найден ни в env, ни в config.toml, ни в secrets.toml!")
            loguru_logger.debug(f"Динамическая подгрузка токена: {token[:5]}...")
            return SecretStr(token)
        if isinstance(v, SecretStr):
            return v
        if isinstance(v, str):
            return SecretStr(v)
        raise ValueError("token должен быть строкой или SecretStr")

    @property
    def TOKEN(self) -> str | SecretStr:
        """Свойство для получения токена бота."""
        if isinstance(self.token, SecretStr):
            return self.token
        # fallback, если вдруг что-то пошло не так
        loguru_logger.debug(f"{self.token.get_secret_value()[:5]}")
        return SecretStr(str(self.token))

    @property
    def ADMINS(self) -> Set[int]:
        """Свойство для получения списка администраторов."""
        return self.admins
    @property
    def SUPERUSERS(self) -> Set[int]:
        """Свойство для получения списка суперпользователей."""
        return self.superusers
    @property
    def ROLE_ACCESS(self) -> Dict[str, List[str]]:
        """Свойство для получения прав доступа по ролям."""
        return self.role_access
    @computed_field
    def RATE_LIMIT(self) -> float:
        """Свойство для получения лимита запросов в секунду."""
        return self.rate_limit

    @field_validator("admins", "superusers", mode="before")
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

    @field_validator("role_access", mode="before")
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
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="BOT_",
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        secrets_dir=str(DATA_DIR / "secrets"),
        env_nested_delimiter="__",)


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
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        case_sensitive=True,
        extra="ignore",
        secrets_dir=str(DATA_DIR / "secrets"),
        env_nested_delimiter="__",
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
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        env_prefix="MONGO_",
        case_sensitive=True,
        extra="ignore",
        secrets_dir=str(DATA_DIR / "secrets"),
        env_nested_delimiter="__",
    )


class NetworkConfig(BaseSettings):
    PING_COUNT: int = Field(default=4, env="NETWORK_PING_COUNT")
    PING_INTERVAL: int = Field(default=2, env="NETWORK_PING_INTERVAL")
    PING_TIMEOUT: int = Field(default=10, env="NETWORK_PING_TIMEOUT")
    SNMP_RO: list[str] = Field(default_factory=list, env="NETWORK_SNMP_RO")
    SNMP_RW: list[str] = Field(default_factory=list, env="NETWORK_SNMP_RW")

    model_config = SettingsConfigDict(
        env_prefix="NETWORK_",
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        secrets_dir=str(DATA_DIR / "secrets"),
        env_nested_delimiter="__",
    )


class MiscConfig(BaseSettings):
    """Настройки Miscellaneous.
    Содержит дополнительные параметры, которые не относятся к основным секциям
    """

    # Параметры, которые могут быть переопределены в .env или secrets.toml
    TIMEZONE: str = Field(default="UTC", env="TIMEZONE")
    MAX_PAYLOAD_SIZE_MB: int = Field(default=10, env="MAX_PAYLOAD_SIZE_MB")
    EXCLUDED_SUBSTRINGS: Optional[str] = Field(default="", env="EXCLUDED_SUBSTRINGS")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        toml_file=str(CONFIG_PATH),
        case_sensitive=True,
        extra="ignore",
    )


class Settings(BaseSettings):
    """
    Конфигурация приложения.
    Секреты — из .env или Docker-секретов. Параметры — из config.toml.
    """

    DEBUG: bool = Field(default=False, env="DEBUG")
    version: str = Field(default=__version__, description="Версия приложения")
    use_redis: bool = Field(
        default=False, env="USE_REDIS", description="Использовать Redis для кэширования",
        alias="use_redis",
    )
    use_mongo: bool = Field(
        default=False,
        env="USE_MONGO",
        description="Использовать MongoDB для хранения данных",
        alias="use_mongodb",
    )
    use_fs: bool = Field(
        default=False,
        env="USE_FS",
        description="Использовать файловую систему для хранения данных",
        alias="use_fs",
    )
    use_firebase: bool = Field(
        default=False,
        env="USE_FIREBASE",
        description="Использовать Firebase для хранения данных",
        alias="use_firebase",
    )
    use_cache: bool = Field(
        default=False,
        env="USE_CACHE",
        description="Использовать кэширование",
        alias="use_cache",
    )

    app: AppSettings = Field(
        default_factory=AppSettings,
        description="Настройки приложения",
    )
    db: DataBaseSettings = Field(
        default_factory=DataBaseSettings,
        description="Настройки базы данных",
    )
    api: APISettings = Field(
        default_factory=APISettings,
        description="Настройки API",
    )
    bot: BotConfig = Field(
        default_factory=BotConfig,
        description="Настройки бота",
    )
    redis: Optional[RedisConfig] = None
    mongo: Optional[MongoDBConfig] = None
    net: NetworkConfig = Field(
        default_factory=NetworkConfig,
        description="Настройки сети и подключения",
    )

    misc: MiscConfig = Field(
        default_factory=MiscConfig,
        description="Дополнительные параметры конфигурации",
    )
    security: Security = Field(
        default_factory=Security,
        description="Настройки безопасности приложения",
    )

    @computed_field
    @property
    def VERSION(self) -> str:
        return __version__

    @property
    def USE_REDIS(self) -> bool:
        return self.use_redis

    @property
    def USE_MONGODB(self) -> bool:
        return self.use_mongo

    @property
    def USE_FS(self) -> bool:
        return self.use_fs

    @property
    def USE_FIREBASE(self) -> bool:
        return self.use_firebase

    @property
    def USE_CACHE(self) -> bool:
        return self.use_cache

    @model_validator(mode="after")
    def conditional_redis_load(self):
        self.redis = RedisConfig() if self.USE_REDIS else None
        return self

    @model_validator(mode="after")
    def conditional_mongo_load(self):
        self.mongo = MongoDBConfig() if self.USE_MONGODB else None
        return self

    # @model_validator(mode="after")
    # def conditional_fs_load(cls, values):
    #     values.fs = values.USE_FS
    #     return values
    # @model_validator(mode="after")
    # def conditional_firebase_load(cls, values):
    #     values.firebase = values.USE_FIREBASE
    #     return values
    # @model_validator(mode="after")
    # def conditional_cache_load(cls, values):
    #     values.cache = values.USE_CACHE
    #     return values

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_PATH),
        env_file=str(ENV_PATH),
        env_nested_delimiter="__",
        extra="ignore",
        secrets_dir=DATA_DIR / "secrets",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type["Settings"],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ) -> Tuple:
        # Порядок: TOML (общие параметры) → .env → ENV → Docker-секреты
        return (
            TomlConfigSettingsSource(settings_cls),
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    def validate_all(self):
        # Проверка Redis
        if self.USE_REDIS:
            if not self.redis:
                raise ValueError("USE_REDIS=True, но секция redis не инициализирована!")
            if not self.redis.HOST or not self.redis.PORT:
                raise ValueError("Redis: HOST и PORT обязательны при USE_REDIS=True")
            if self.redis.PASSWORD is None:
                loguru_logger.warning("Redis: пароль не задан (это допустимо, но не рекомендуется для production)")

        # Проверка MongoDB
        if self.USE_MONGODB:
            if not self.mongo:
                raise ValueError("USE_MONGODB=True, но секция mongo не инициализирована!")
            if not self.mongo.DB_NAME:
                raise ValueError("MongoDB: DB_NAME обязателен при USE_MONGODB=True")

        # Пример: если включён TFA, то должен быть секрет
        if hasattr(self, "security") and getattr(self.security, "tfa_enable", False):
            if not self.security.tfa or not self.security.tfa.secret:
                raise ValueError("TFA включён, но секрет не задан!")

        # Можно добавить другие проверки по необходимости

        loguru_logger.info("Проверка целостности конфигурации пройдена успешно.")

# Инициализация конфигурации
settings = Settings()
settings.validate_all()


# Определение режима DEBUG с резервом на ENV
def resolve_debug_mode() -> bool:
    return bool(settings.DEBUG) or os.getenv("DEBUG", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


debug_mode = resolve_debug_mode()

# Инициализация логгера
logger = LoggerManager(name=APP_ROLE, debug=debug_mode).get_logger()


