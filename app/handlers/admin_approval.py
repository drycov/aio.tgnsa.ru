from aiogram import Router, F
from aiogram.types import Message

from app.bot_instance import bot
from app.constants import Messages
from app.models import User

router = Router()


@router.message(lambda message: F.text.startswith('/approve_') or F.text.startswith('/reject_'))
async def admin_approval(message: Message):
    try:
        action, user_id = message.text.split('_', 1)  # Используем split с maxsplit=1
    except ValueError:
        # Обрабатываем случай, когда в message.text нет разделителя "_"
        await message.answer("Некорректный формат команды.")
        return
    user_id = int(user_id)

    if action == '/approve':
        user = User.get_by_tg_id(user_id)
        if user:
            user.update({"is_verified": True, "is_allowed": True})
            await bot.send_message(user_id, Messages.USER_ALLOWED_IN_DB.value)
            await message.answer(Messages.USER_ADDED.value)
    elif action == '/reject':
        User.delete(user_id)
        await bot.send_message(user_id, Messages.USER_REJECTED_FROM_DB.value)
        await message.answer(Messages.USER_REJECTED.value)
