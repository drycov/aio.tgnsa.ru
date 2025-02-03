"""
Этот модуль инициализирует экземпляр бота, включая хранилище, диспетчер и локальные настройки.
"""

import locale

import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.redis import RedisStorage
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi
from redis.exceptions import RedisError

from bot.utils import HelperFunctions
from bot.utils.logger_instance import app_logger
from config import Config
from ertm import ERTM

# Устанавливаем режим парсинга HTML по умолчанию
parse_mode = DefaultBotProperties(parse_mode=ParseMode.HTML)

def initialize_storage():
    """
    Инициализация хранилища FSM с поддержкой Redis, MongoDB или памяти.
    """
    try:
        if Config.USE_REDIS:
            redis_client = redis.from_url(Config.REDIS_URL)
            app_logger.info("Redis-клиент успешно подключен")
            return RedisStorage(redis_client)
        elif Config.USE_MONGODB:
            mongo_client = AsyncIOMotorClient(Config.MONGO_URI, server_api=ServerApi('1'))
            app_logger.info("MongoDB-клиент успешно подключен")
            return MongoStorage(mongo_client, db_name=Config.MONGO_DB_NAME)
        else:
            app_logger.warning("Redis или MongoDB не настроены, используется MemoryStorage")
            return MemoryStorage()
    except (RedisError, PyMongoError) as ex:
        HelperFunctions.log_error(action="initialize_storage", error=ex)
        app_logger.warning("Ошибка подключения, используется MemoryStorage")
        return MemoryStorage()

# Инициализация хранилища FSM
app_logger.info("Инициализация хранилища FSM")
storage = initialize_storage()

# Инициализация бота и диспетчера
bot = Bot(token=Config.API_TOKEN, default=parse_mode)
dp = Dispatcher(storage=storage)

# Установка локали
locale.setlocale(locale.LC_TIME, Config.DEFAULT_LOCALE)

# Инициализация ERTM
ertm = ERTM()
