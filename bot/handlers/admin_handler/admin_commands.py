import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.bot_instance import bot
from bot.constants import Messages, MenuLabels
from bot.constants.states import MainCommands
from bot.keyboards import admin_menu, system_info_menu
from bot.models import User
from bot.utils import StateManager

router = Router()

# Регулярное выражение для проверки формата команды
command_pattern = re.compile(r"^/(approve|reject)_(\d+)$")


@router.message(F.text == MenuLabels.ADMIN_PANEL.value)
async def admin_panel_command(message: Message, state: FSMContext):
    keyboard = admin_menu()  # Создаем клавиатуру для администратора
    display_data = {"text": "Администрирование.", "reply_markup": keyboard}
    await StateManager.set_state_with_previous(state, MainCommands.ADMIN_PANEL, display_data)
    await message.answer(**display_data)


@router.message(F.text == "Статус системы")
async def system_panel_command(message: Message, state: FSMContext):
    keyboard = system_info_menu()  # Создаем клавиатуру для администратора
    display_data = {"text": "Статус системы."}
    await StateManager.set_state_with_previous(state, MainCommands.SYSTEM_MENU, display_data)
    await message.answer(**display_data, reply_markup=keyboard)


@router.message(lambda message: message.text and command_pattern.match(message.text))
async def admin_approval(message: Message):
    match = command_pattern.match(message.text)
    if not match:
        await message.answer("Некорректный формат команды.")
        return

    action, user_id = match.groups()
    user_id = int(user_id)

    # Получаем пользователя по Telegram ID
    user = User.get_by_tg_id(user_id)
    if not user:
        await message.answer(f"Пользователь с ID {user_id} не найден.")
        return

    if action == "approve":
        user.update({"is_verified": True, "is_allowed": True})
        await bot.send_message(user_id, Messages.USER_ALLOWED_IN_DB.value)
        await message.answer(Messages.USER_ADDED.value)
    elif action == "reject":
        User.delete(user_id)
        await bot.send_message(user_id, Messages.USER_REJECTED_FROM_DB.value)
        await message.answer(Messages.USER_REJECTED.value)
