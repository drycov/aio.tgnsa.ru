import logging
import json
from typing import Any
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from rich import print

logger = logging.getLogger(__name__)


def log_model_init(cls):
    """Логирует создание моделей Pydantic (без секретов)."""
    orig_init = cls.__init__

    def safe_model_dump(instance: BaseSettings) -> dict:
        def safe_val(val: Any):
            if isinstance(val, SecretStr):
                return "********"
            if isinstance(val, set):
                return list(val)
            if isinstance(val, BaseSettings):
                return safe_model_dump(val)
            if isinstance(val, dict):
                return {k: safe_val(v) for k, v in val.items()}
            if isinstance(val, list):
                return [safe_val(i) for i in val]
            return val
        return {k: safe_val(v) for k, v in instance.model_dump().items()}

    def new_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        try:
            dumped = json.dumps(safe_model_dump(self), indent=2, ensure_ascii=False)
        except Exception as e:
            dumped = f"[Ошибка сериализации]: {e}"
        print(f"[🔧 Init] {cls.__name__}:\n{dumped}")
        logger.debug(f"[🔧 Init] {cls.__name__}:\n{dumped}")

    cls.__init__ = new_init
    return cls
