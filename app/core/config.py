import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.logger_manager import LoggerManager

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# --- Load .env ---
load_dotenv(dotenv_path=ENV_PATH)


class BaseConfig(BaseSettings):
    DEBUG: bool = Field(default=False, env="DEBUG")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
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


# Инициализация временной базовой конфигурации для доступа к DEBUG
_base_config = BaseConfig()

# --- Logging ---
debug_mode = _base_config.DEBUG in ("1", "true", "yes")
logger = LoggerManager(name="config", debug=debug_mode).get_logger()


class Settings(BaseSettings):
    USE_REDIS: bool = Field(default=False, env="USE_REDIS")
    bot: BotConfig = Field(default_factory=BotConfig)

    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
    )

logger.info(BASE_DIR)
settings = Settings()
