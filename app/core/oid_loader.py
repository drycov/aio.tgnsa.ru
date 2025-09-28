import json
import tomli
from pathlib import Path
from typing import Dict, Any
from app.core.patchs import STATIC_DIR

TOML_PATH = STATIC_DIR / "oids" / "oids.toml"
JSON_PATH = STATIC_DIR / "oids" / "oids.json"

import logging

logger = logging.getLogger(__name__)
class OIDLoader:
    _cached_oids: Dict[str, Any] = {}

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Загрузка OID-ов: из TOML с автогенерацией JSON."""
        if cls._cached_oids:
            return cls._cached_oids

        # # 1. Попытка загрузки JSON
        if JSON_PATH.exists():
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    cls._cached_oids = json.load(f)
                    logger.debug("Загружено из oids.json")
                    return cls._cached_oids
            except Exception as e:
                logger.warning(f"Ошибка чтения oids.json: {e}")

        # 2. Fallback: загрузка из TOML
        if TOML_PATH.exists():
            try:
                with open(TOML_PATH, "rb") as f:
                    cls._cached_oids = tomli.load(f)
                    logger.debug("Загружено из oids.toml")

                    # Автогенерация JSON
                    with open(JSON_PATH, "w", encoding="utf-8") as jf:
                        json.dump(cls._cached_oids, jf, indent=4, ensure_ascii=False)
                        logger.info("Автосоздан oids.json из oids.toml")

                    return cls._cached_oids
            except Exception as e:
                logger.error(f"Ошибка чтения oids.toml: {e}")

        logger.critical("Не удалось загрузить конфигурацию OID-ов")
        return {}
