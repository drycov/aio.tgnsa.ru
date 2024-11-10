# bot/handlers/start_handler.py
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import Messages
from app.constants.states import MainCommands, ALL_STATES
from app.keyboards import on_enter_keyboard
from app.utils import StateManager, CalendarMarkup

# Создаем маршрутизатор для регистрации обработчиков
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()  # Сбрасываем состояние для чистого начала

    display_data = {"text": Messages.PLEASE_ENTER.value, "reply_markup": on_enter_keyboard}

    # Устанавливаем состояние и сохраняем display_data через StateManager
    await StateManager.set_state_with_previous(state, MainCommands.START, display_data)

    # Отправляем сообщение с данными для отображения
    await message.answer(**display_data)

    # Удаляем предыдущее сообщение пользователя (если это нужно по логике)
    await message.delete()


# Обработчик для команды /cancel, который отменяет текущее состояние
@router.message(F.text == "/cancel", StateFilter(*ALL_STATES))
async def cancel_command(message: Message, state: FSMContext):
    await StateManager.handle_back_action(state, message)

    # Удаляем предыдущее сообщение пользователя (если это нужно по логике)
    await message.delete()
    await state.clear()


@router.message(F.text == "/schedule")
async def schedule_command(message: Message):
    now = datetime.now()
    calendar_markup = CalendarMarkup(now.year, now.month).create_calendar()

    await message.answer("Выберите дату для планирования работ:",
                         reply_markup=calendar_markup)
