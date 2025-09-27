from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.bot.fsm.state_manager import StateManager
from app.core.logging_setup import configure_logger
from app.core.utils.decorators import safe_delete_message
from ..constants.menu_label import DutyMenuLabels,DUTY_MENU_STRUCTURE
from ..constants.messsages import DutyMessages
from ..constants.menu import get_menu_buttons
from ..constants.states import DutyStates
import logging

logger = configure_logger().bind(component=f"{__name__}")
# 🔧 Универсальная утилита
async def _set_state_and_respond(
    state: FSMContext,
    new_state,
    message: Message,
    text: str,
    reply_markup=None,
    extra_data: dict | None = None,
):
    display_data = {"text": text}
    if reply_markup:
        display_data["reply_markup"] = reply_markup

    await StateManager.set_state_with_history(state, new_state, display_data)
    await message.answer(**display_data)
    if extra_data:
        await state.update_data(**extra_data)

def register_handlers(router: Router):
    @router.message(F.text == DutyMenuLabels.MAIN.value)
    @safe_delete_message
    async def duty_menu_handler(message: Message, state: FSMContext):
        """
        Хендлер входа в меню дежурств.
        """
        try:
            logger.info(f"[duty_menu] Пользователь {message.from_user.id} открыл Duty меню")

            # Кнопки меню
            buttons = get_menu_buttons(DUTY_MENU_STRUCTURE)

            await _set_state_and_respond(
                state=state,
                new_state=DutyStates.MENU,
                message=message,
                text="📅 <b>Меню дежурств</b>\nВыберите действие:",
                reply_markup=buttons,
                extra_data={"section": "duty_menu"},
            )

        except Exception as e:
            logger.exception(f"[duty_menu_handler] Ошибка: {e}")
            await message.answer(DutyMessages.ERROR_UNKNOWN.value)



