# bot/handlers/message_handler.py
from aiogram import Router
from aiogram.types import Message

# Создаем маршрутизатор для регистрации обработчиков
router = Router()

@router.message()
async def message_handler(msg: Message):
    await msg.answer(f"Твой ID: {msg.from_user.id}")
