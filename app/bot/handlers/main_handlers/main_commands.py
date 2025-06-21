from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants.labels import MenuLabels
from app.bot.constants.messages import Messages
from app.bot.fsm.state_manager import StateManager
from app.bot.fsm.states.main import MAINState
from app.bot.keyboards.base import on_enter_keyboard
from app.bot.keyboards.main import generate_main_keyboard
from app.core.config import logger
from app.exceptions.exceptions import UserNotFoundError
from app.services.user import UserSearchField, UserService

router = Router()


@router.message(F.text == MenuLabels.ENTER.value)
async def main_menu(
    message: Message,
    state: FSMContext,
    session: AsyncSession,  # сюда будет передана реальная сессия
):
    tg_id = message.from_user.id
    service = UserService(session)
    try:
        user = await service.get_user(tg_id, UserSearchField.TG_ID)
    except UserNotFoundError:
        logger.warning(f"[main_menu] User not found: tg_id={tg_id}")
        await message.answer(Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard)
        return
    except Exception as e:
        logger.exception(f"[main_menu] Error loading user: {e}")
        await message.answer(Messages.INTERNAL_ERROR.value)
        return

    keyboard = generate_main_keyboard(user.is_admin_user())
    display = {"text": Messages.WELCOME.value, "reply_markup": keyboard}
    await message.answer(**display)
    await StateManager.set_state_with_previous(state, MAINState.MAIN, display_data=display)
    await state.update_data(
        user_id=tg_id,
        is_online=True,
        is_admin=user.is_admin_user(),
        token=user.generate_jwt(tg_id),
    )

    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"[main_menu] Failed to delete user message: {e}")


@router.message(F.text == MenuLabels.EXIT.value)
async def exit_command(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    try:
        await message.delete()
    except Exception as e:
        logger.warning(
            f"[exit_command] Failed to delete exit trigger message: {e}")

    try:
        await message.answer(Messages.GOODBYE.value, reply_markup=ReplyKeyboardRemove())
        await state.clear()

        await message.answer(Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard)
        await state.set_state(MAINState.MAIN)

        await state.update_data(
            user_id=tg_id,
            is_online=False,
            is_admin=False,
            token=""
        )
    except Exception as e:
        logger.exception(f"[exit_command] Unexpected error: {e}")
