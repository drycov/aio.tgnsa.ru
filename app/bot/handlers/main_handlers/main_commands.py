from aiogram import F, Router, types
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
from app.core.db import get_session
from app.services.user import UserSearchField, UserService

router = Router()


@router.message(F.text == MenuLabels.ENTER.value)
async def main_menu(message: Message, state: FSMContext, session: AsyncSession):

    try:
        session_instance = await anext(session)

        service = UserService(session_instance)
        user = await service.get_user(message.from_user.id, UserSearchField.TG_ID)
        role = await service.get_user(message.from_user.id, UserSearchField.ROLE)
        if not user:
            logger.warning("main_menu: user not found in data")
            await message.answer(Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard)
            return

        tg_id = message.from_user.id
        keyboard = generate_main_keyboard(user.is_admin_user())
        display = {"text": Messages.WELCOME.value, "reply_markup": keyboard}
        await message.answer(**display)
        await StateManager.set_state_with_previous(state, MAINState.MAIN, display_data=display)
        await state.update_data(user_id=tg_id, is_online=True, token=user.generate_jwt(tg_id), is_admin=user.is_admin_user())
        await message.delete()
    except Exception as e:
        logger.warning(f"Failed deleting message: {e}")
    finally:
        await session.aclose()


@router.message(F.text == MenuLabels.EXIT.value)
async def exit_command(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Failed deleting exit trigger message: {e}")

    display = {"text": Messages.GOODBYE.value,
               "reply_markup": ReplyKeyboardRemove()}
    await message.answer(**display)
    await state.clear()

    await message.answer(Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard)
    await state.set_state(MAINState.MAIN)
    await state.update_data(user_id=message.from_user.id, is_online=False, is_admin=False, token="")
