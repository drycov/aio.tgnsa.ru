import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.logger_manager import LoggerManager

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
SUPPORTED_ENGINES = {"sqlite", "postgres", "mysql", "mariadb"}

# --- Load .env early ---
load_dotenv(dotenv_path=ENV_PATH)

# --- Role setup from env ---
APP_ROLE = os.getenv("APP_ROLE", "app")


class PostgresConfig(BaseSettings):
    HOST: str = Field(..., env="POSTGRES_HOST")
    PORT: int = Field(5432, env="POSTGRES_PORT")
    USER: str = Field(..., env="POSTGRES_USER")
    PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    NAME: str = Field(..., env="POSTGRES_DB")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="POSTGRES_",
    )


class SqliteConfig(BaseSettings):
    FILE: str = Field("app.db", env="SQLITE_FILE")

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
    PASSWORD: str = Field(..., env="MYSQL_PASSWORD")
    NAME: str = Field(..., env="MYSQL_DB")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="MYSQL_",
    )


class BotConfig(BaseSettings):
    TOKEN: str

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="BOT_",
    )


class Settings(BaseSettings):
    USE_REDIS: bool = Field(default=False, env="USE_REDIS")
    DB_ENGINE: Literal["sqlite", "postgres", "mysql"] = Field(
        default="sqlite", env="DB_ENGINE")
    DEBUG: bool = Field(default=False, env="DEBUG")
    bot: BotConfig = Field(default_factory=BotConfig)

    postgres: PostgresConfig | None = None
    sqlite: SqliteConfig | None = None
    mysql: MySQLConfig | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def get_db_config(self):
        if self.DB_ENGINE == "postgres":
            return self.postgres or PostgresConfig()
        elif self.DB_ENGINE == "sqlite":
            return self.sqlite or SqliteConfig()
        elif self.DB_ENGINE == "mysql":
            return self.mysql or MySQLConfig()
        else:
            raise ValueError(
                f"❌ DB_ENGINE={self.DB_ENGINE} не поддерживается.")


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

# --- Validators ---

if settings.DB_ENGINE not in SUPPORTED_ENGINES:
    raise ValueError(f"❌ DB_ENGINE={settings.DB_ENGINE} не поддерживается.")
