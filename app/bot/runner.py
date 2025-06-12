# app/bot/runner.py
import asyncio
from aiogram import Bot, Dispatcher
from core.config import settings, logger

TOKEN = "your_bot_token"
bot = Bot(token=settings.bot.TOKEN)
dp = Dispatcher()

async def main():
    print("🤖 Запуск бота...")
    await dp.start_polling(bot)

def run_bot():
    asyncio.run(main())
