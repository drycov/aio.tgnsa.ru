import contextlib

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.fsm.state_manager import StateManager
from app.bot.fsm.states.base import CMDState
from app.bot.keyboards.main import generate_main_keyboard  # <- обновлено

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()  # Полный сброс FSM состояния

    # Пример: авторизация не реализована, по умолчанию — гость
    is_admin = False  # <- здесь можно подключить реальную логику проверки

    display_data = {
        "text": f"👋 Привет, {message.from_user.full_name}!\nДобро пожаловать.",
        "reply_markup": generate_main_keyboard(is_admin)
    }

    # Установка состояния с сохранением истории
    await StateManager.set_state_with_previous(state, CMDState.CMD_START, display_data)

    # Отправка приветственного сообщения
    await message.answer(**display_data)

    # Удаление команды /start (если нужно)
    with contextlib.suppress(Exception):
        await message.delete()

