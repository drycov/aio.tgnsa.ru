import redis.asyncio as redis
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.exceptions import RedisError

from app.bot.fsm.file_storage import FileStorage
from app.core.config import logger, settings
from app.core.config import DATA_DIR

from pathlib import Path


def initialize_storage():
    """
    Инициализация FSM-хранилища с поддержкой Redis, файловой системы и fallback на память.
    """
    try:
        if settings.USE_REDIS:
            redis_client = redis.from_url(settings.redis.dsn())
            logger.info("✅ Используется RedisStorage")
            return RedisStorage(redis_client)

        elif settings.USE_FS:
            storage_dir = Path(DATA_DIR) / ".fsm_states"
            storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📂 Используется FileStorage: {storage_dir}")
            return FileStorage(base_path=str(storage_dir), format="json")

        else:
            logger.warning(
                "⚠️ Redis и FileStorage отключены, используется MemoryStorage"
            )
            return MemoryStorage()

    except (RedisError, OSError) as ex:
        logger.warning(
            f"❌ Ошибка инициализации хранилища: {ex}, fallback на MemoryStorage"
        )
        return MemoryStorage()
