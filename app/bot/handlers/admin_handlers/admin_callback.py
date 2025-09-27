from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from app.core.config import settings
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.services.registration_buffer import RegistrationBuffer

import logging

logger = logging.getLogger(__name__)
router = Router()

OWNER_ID = settings.bot.OWNER_ID  # ID владельца из конфигурации


async def is_chat_available(bot, user_id: int) -> bool:
    """Проверяет, доступен ли чат с пользователем."""
    try:
        await bot.get_chat(user_id)
        return True
    except (TelegramBadRequest, TelegramForbiddenError):
        return False


@router.callback_query(F.data.startswith("admin:confirm:"))
async def handle_admin_approve(callback: CallbackQuery, db: AsyncSession):
    """Подтверждение регистрации админом."""
    try:
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.answer("❌ Некорректный callback.")
            return

        user_id = int(parts[2])
        admin_id = callback.from_user.id

        # Получение данных из буфера
        user_data = await RegistrationBuffer.get(user_id)
        if not user_data:
            await callback.message.answer("❌ Данные пользователя не найдены.")
            await callback.answer()
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
            password="telegram",  # TODO: заменить на генерацию пароля
        )

        await user_service.create_user(user_create)
        await RegistrationBuffer.delete(user_id)

        if await is_chat_available(callback.bot, user_id):
            await callback.bot.send_message(
                user_id,
                "✅ Ваша регистрация подтверждена администратором.\nТеперь вы можете пользоваться ботом.",
            )

        await callback.message.edit_text("✅ Регистрация пользователя подтверждена.")
        logger.info(f"[admin_approve] 👤 Пользователь {user_id} подтверждён админом {admin_id}")

    except Exception as e:
        logger.exception(f"[admin_approve] ❌ Ошибка при подтверждении: {e}")
        await callback.message.answer("❌ Ошибка при подтверждении регистрации.")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("admin:cancel:"))
async def handle_admin_reject(callback: CallbackQuery):
    """Отклонение регистрации админом."""
    try:
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.answer("❌ Некорректный callback.")
            return

        user_id = int(parts[2])
        admin_id = callback.from_user.id

        if await is_chat_available(callback.bot, user_id):
            await callback.bot.send_message(
                user_id,
                "❌ Ваша регистрация была отклонена администратором.\nПо вопросам обратитесь в поддержку.",
            )

        await callback.message.edit_text("❌ Регистрация пользователя отклонена.")
        await RegistrationBuffer.delete(user_id)

        logger.info(f"[admin_reject] 👤 Пользователь {user_id} отклонён админом {admin_id}")

    except Exception as e:
        logger.error(f"[admin_reject] ❌ Ошибка при отклонении: {e}")
        await callback.message.answer("❌ Ошибка при отклонении регистрации.")
    finally:
        await callback.answer()


@router.message(F.text == "/admins")
async def check_admins_status(message: Message):
    """Проверка доступности всех админов ботом."""
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ Команда доступна только владельцу бота.")
        return

    results = []
    for admin_id in settings.bot.ADMINS:
        status = "✅ доступен" if await is_chat_available(message.bot, admin_id) else "❌ не доступен"
        results.append(f"<code>{admin_id}</code> — {status}")

    text = "🛡 Статус администраторов:\n\n" + "\n".join(results)
    await message.answer(text, parse_mode="HTML")
