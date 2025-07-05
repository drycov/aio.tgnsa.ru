from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from app.core.config import settings

from app.schemas.user import UserCreate
from app.services.user import UserService
from app.services.registration_buffer import (
    RegistrationBuffer,
)  # 👈 временное хранилище данных (см. ниже)

import logging

logger = logging.getLogger(__name__)

router = Router()
OWNER_ID = settings.bot.OWNER_ID  # Установите ID владельца в конфигурации


@router.callback_query(F.data.startswith("admin:confirm:"))
async def handle_admin_approve(callback: CallbackQuery, db: AsyncSession):
    try:
        user_id = int(callback.data.split(":")[2])

        # Получение данных из буфера регистрации (не FSM)
        user_data = await RegistrationBuffer.get(user_id)
        if not user_data:
            await callback.message.answer("❌ Данные пользователя не найдены.")
            return

        user_service = UserService(db)

        user_create = UserCreate(
            tg_id=user_id,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            department=user_data.get("department"),
            company_post=user_data.get("company_post"),
            phone=user_data.get("phone_number"),
            email=user_data.get("email"),
            password="telegram",  # можно заменить на генерацию
        )

        await user_service.create_user(user_create)

        # Очистить буфер
        await RegistrationBuffer.delete(user_id)

        await callback.bot.send_message(
            user_id,
            "✅ Ваша регистрация подтверждена администратором.\nТеперь вы можете пользоваться ботом.",
        )
        await callback.message.edit_text("✅ Вы подтвердили регистрацию пользователя.")
        logger.info(f"[admin_approve] Пользователь {user_id} создан и подтверждён.")

    except Exception as e:
        logger.exception(f"[admin_approve] Ошибка при создании пользователя: {e}")
        await callback.message.answer("❌ Ошибка при подтверждении регистрации.")


@router.callback_query(F.data.startswith("admin:cancel:"))
async def handle_admin_reject(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split(":")[2])

        await callback.bot.send_message(
            user_id,
            "❌ Ваша регистрация была отклонена администратором.\nПо вопросам обратитесь в поддержку.",
        )
        await callback.message.edit_text("❌ Вы отклонили регистрацию пользователя.")
        logger.info(f"[admin_reject] Пользователь {user_id} отклонён администратором.")

        # Очистка буфера (если нужен)
        await RegistrationBuffer.delete(user_id)

    except Exception as e:
        logger.error(f"[admin_reject] Ошибка при отправке сообщения: {e}")
        await callback.message.answer(
            "❌ Не удалось отправить уведомление пользователю."
        )

async def is_chat_available(bot, user_id: int) -> bool:
    try:
        await bot.get_chat(user_id)
        return True
    except (TelegramBadRequest, TelegramForbiddenError):
        return False

@router.message(F.text == "/admins")
async def check_admins_status(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ Команда доступна только владельцу бота.")
        return

    results = []
    for admin_id in settings.bot.ADMINS:
        status = "✅ доступен" if await is_chat_available(message.bot, admin_id) else "❌ не доступен"
        results.append(f"<code>{admin_id}</code> — {status}")

    text = "🛡 Статус администраторов:\n\n" + "\n".join(results)
    await message.answer(text, parse_mode="HTML")