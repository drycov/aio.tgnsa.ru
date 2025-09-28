from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants.labels import MenuLabels
from app.bot.constants.messages import Messages
from app.bot.fsm.state_manager import StateManager
from app.bot.fsm.states.main import MAINState
from app.bot.keyboards.base import build_auth_keyboard
from app.bot.keyboards.main import generate_main_keyboard
from app.core.logging_setup import configure_logger
from app.exceptions.exceptions import UserNotFoundError
from app.services.user import UserSearchField, UserService
from app.bot.handlers.register_handlers.registration_handler import start_registration
from app.core.utils.decorators import safe_delete_message

router = Router()
logger = configure_logger().bind(component="MainMenuHandlers")


@router.message(F.text.casefold() == MenuLabels.ENTER.value.casefold())
@safe_delete_message
async def main_menu(message: Message, state: FSMContext, db: AsyncSession):
    """
    Entry point into main menu:
      - Проверяет авторизацию пользователя.
      - Регистрирует нового пользователя при необходимости.
      - Открывает главное меню.
    """
    tg_id = message.from_user.id
    service = UserService(db)

    try:
        user = await service.get_user(tg_id, UserSearchField.TG_ID)
        if not user.is_authorized:
            await service.set_authorized(tg_id, True)

    except UserNotFoundError:
        logger.warning(f"[main_menu] 🚫 User not found: tg_id={tg_id}")
        keyboard = build_auth_keyboard(False)

        await message.answer(Messages.PLEASE_ENTER.value, reply_markup=keyboard)
        await start_registration(message, state)
        return

    except Exception as e:
        logger.exception(f"[main_menu] ❌ Unexpected error: {e}")
        await message.answer(Messages.INTERNAL_ERROR.value)
        return

    # --- Authorized flow ---
    is_admin = await service.is_admin(tg_id)
    keyboard = generate_main_keyboard(is_admin)

    display = {"text": Messages.WELCOME.value, "reply_markup": keyboard}
    await message.answer(**display)

    await StateManager.set_state_with_history(
        state, MAINState.MAIN, display_data=display
    )

    await state.update_data(
        user_id=tg_id,
        is_online=True,
        is_admin=is_admin,
        token=user.generate_jwt(),
    )

    logger.info(f"[main_menu] ✅ User {tg_id} вошёл в систему (admin={is_admin})")


@router.message(F.text.casefold() == MenuLabels.EXIT.value.casefold())
@safe_delete_message
async def exit_command(message: Message, state: FSMContext, db: AsyncSession):
    """
    Exit command:
      - Сбрасывает состояние и авторизацию.
      - Отправляет клавиатуру входа.
    """
    tg_id = message.from_user.id
    service = UserService(db)

    try:
        # Сообщение "прощания"
        await message.answer(Messages.GOODBYE.value, reply_markup=ReplyKeyboardRemove())

        # Очистка state
        await state.clear()
        await state.set_state(MAINState.MAIN)
        await state.update_data(user_id=tg_id, is_online=False, is_admin=False, token="")

        # Сброс авторизации
        user = await service.get_user(tg_id, UserSearchField.TG_ID)
        await service.set_authorized(tg_id, False)

        # Обновлённый объект
        user = await service.get_user(tg_id, UserSearchField.TG_ID)

        keyboard = build_auth_keyboard(user.is_authorized)
        await message.answer(Messages.PLEASE_ENTER.value, reply_markup=keyboard)

        logger.info(f"[exit_command] 👋 User {tg_id} вышел из системы")

    except Exception as e:
        logger.exception(f"[exit_command] ❌ Unexpected error: {e}")
        await message.answer(Messages.INTERNAL_ERROR.value)
