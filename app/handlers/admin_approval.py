import re

from aiogram import Router
from aiogram.types import Message

from app.bot_instance import bot
from app.constants import Messages
from app.models import User

router = Router()

# Регулярное выражение для проверки формата команды
command_pattern = re.compile(r"^/(approve|reject)_(\d+)$")


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
