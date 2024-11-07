import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import Config

parse_mode = DefaultBotProperties(parse_mode=ParseMode.HTML)
redis_client = redis.from_url(Config.REDIS_URL)

storage = RedisStorage(redis_client)
bot = Bot(token=Config.API_TOKEN, default=parse_mode)
dp = Dispatcher(storage=storage)
