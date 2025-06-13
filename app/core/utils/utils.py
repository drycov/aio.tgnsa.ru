import redis.asyncio as redis
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.exceptions import RedisError

from app.core.config import logger, settings

def initialize_storage():
    """
    Инициализация хранилища FSM с поддержкой Redis, MongoDB или памяти.
    """
    try:
        if settings.USE_REDIS:
            redis_client = redis.from_url(settings.redis.dsn())
            logger.info("Redis-клиент успешно подключен")
            return RedisStorage(redis_client)
        else:
            logger.warning(
                "Redis или MongoDB не настроены, используется MemoryStorage")
            return MemoryStorage()
    except (RedisError) as ex:
        logger.warning("Ошибка подключения, используется MemoryStorage")
        return MemoryStorage()
