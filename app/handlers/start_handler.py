# bot/handlers/start_handler.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import Messages
from app.constants.states import MainCommands
from app.keyboards import on_enter_keyboard
from app.utils import StateManager

# Создаем маршрутизатор для регистрации обработчиков
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    display_data = {"text": Messages.PLEASE_ENTER.value, "reply_markup": on_enter_keyboard}

    # Устанавливаем состояние и сохраняем display_data через StateManager
    await StateManager.set_state_with_previous(state, MainCommands.START, display_data)

    # Отправляем сообщение с данными для отображения
    await message.answer(**display_data)

    # Удаляем предыдущее сообщение пользователя (если это нужно по логике)
    await message.delete()
