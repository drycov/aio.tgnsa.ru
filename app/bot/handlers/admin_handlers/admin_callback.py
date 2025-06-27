from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import logger
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.services.registration_buffer import (
    RegistrationBuffer,
)  # 👈 временное хранилище данных (см. ниже)

router = Router()


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
