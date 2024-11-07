# bot/handlers/start_handler.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

# Создаем маршрутизатор для регистрации обработчиков
router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer("Привет! Я помогу тебе узнать твой ID, просто отправь мне любое сообщение.")

@router.message(Command("te"))
async def test_error_handler(msg: Message):
    # Создаем тестовую ошибку (деление на ноль)
    await msg.answer("Сейчас возникнет тестовая ошибка...")
    1 / 0  # Намеренное деление на ноль