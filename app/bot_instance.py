import locale

import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.redis import RedisStorage
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

from app.utils import HelperFunctions
from app.utils.logger_instance import app_logger
from config import Config
from ertm import ERTM

parse_mode = DefaultBotProperties(parse_mode=ParseMode.HTML)


def initialize_storage():
    """
    Инициализация хранилища FSM с поддержкой Redis, MongoDB или памяти.
    """
    try:
        if Config.USE_REDIS:
            redis_client = redis.from_url(Config.REDIS_URL)
            storage = RedisStorage(redis_client)
            app_logger.info("Redis-клиент успешно подключен")
        elif Config.USE_MONGODB:
            # Конфигурация MongoDB
            mongo_client = AsyncIOMotorClient(Config.MONGO_URI, server_api=ServerApi('1'))
            storage = MongoStorage(mongo_client, db_name=Config.MONGO_DB_NAME)
            app_logger.info("MongoDB-клиент успешно подключен")
        else:
            storage = MemoryStorage()
            app_logger.warning("Redis или MongoDB не настроены, используется MemoryStorage")
        return storage
    except Exception as ex:
        HelperFunctions.log_error(action="initialize_storage", error=ex)
        app_logger.warning("Будет использоваться MemoryStorage")
        return MemoryStorage()


storage = initialize_storage()

bot = Bot(token=Config.API_TOKEN, default=parse_mode)
dp = Dispatcher(storage=storage)
locale.setlocale(locale.LC_TIME, Config.DEFAULT_LOCALE)  # Для русского языка, например
ertm = ERTM()
