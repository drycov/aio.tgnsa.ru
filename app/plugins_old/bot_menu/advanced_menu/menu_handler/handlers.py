from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.bot.fsm.state_manager import StateManager
from app.core.logging_setup import configure_logger
from app.core.utils.decorators import safe_delete_message
from ..constants.menu_label import MenuLabels
from ..constants.messsages import Messages
from ..constants.menu import get_advanced_keyboard
from ..constants.states import Advanced

from .advanced_logic import (
    handle_cidr_logic,
    handle_p2p_logic,
    handle_ping_logic,
)

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
    # --- Главное меню ---
    @router.message(F.text == MenuLabels.ADVANCED.value)
    @safe_delete_message
    async def advanced_menu_handler(message: Message, state: FSMContext):
        logger.info(f"[advanced_menu] user_id={message.from_user.id} открыл расширенное меню")

        user_data = await state.get_data()
        is_admin = user_data.get("is_admin", False)

        await state.update_data(opened_advanced=True)

        keyboard = get_advanced_keyboard(is_admin)
        await _set_state_and_respond(state, Advanced.MENU, message, MenuLabels.ADVANCED.value, keyboard)

    # --- CIDR калькулятор ---
    @router.message(F.text == MenuLabels.CIDR_CALC.value)
    async def cidr_calc_command(message: Message, state: FSMContext):
        await _set_state_and_respond(
            state,
            Advanced.CIDR_CALCULATOR,
            message,
            Messages.ENTER_SUBNET.value,
            extra_data={"waiting_for_subnet": True},
        )

    # --- P2P калькулятор ---
    @router.message(F.text == MenuLabels.P2P_CALC.value)
    async def p2p_calc_command(message: Message, state: FSMContext):
        await _set_state_and_respond(
            state,
            Advanced.P2P_CALCULATOR,
            message,
            Messages.ENTER_SUBNET_P2P.value,
            extra_data={"waiting_for_subnet": True},
        )

    # --- Ping устройства ---
    @router.message(F.text == MenuLabels.PING_DEVICE.value)
    async def ping_device_command(message: Message, state: FSMContext):
        await _set_state_and_respond(
            state,
            Advanced.DEVICE_PING,
            message,
            Messages.ENTER_IP.value,
            extra_data={"waiting_for_host": True},
        )

    # --- Обработка CIDR ---
    @router.message(StateFilter(Advanced.CIDR_CALCULATOR))
    async def process_cidr_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_subnet"):
            try:
                await handle_cidr_logic(message, state)
            except Exception as e:
                logger.error(f"[CIDR] Ошибка: {e}", exc_info=True)
                await message.answer("❌ Ошибка при обработке CIDR. Попробуйте снова.")

    # --- Обработка P2P ---
    @router.message(StateFilter(Advanced.P2P_CALCULATOR))
    async def process_p2p_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_subnet"):
            try:
                await handle_p2p_logic(message, state)
            except Exception as e:
                logger.error(f"[P2P] Ошибка: {e}", exc_info=True)
                await message.answer("❌ Ошибка при обработке P2P. Попробуйте снова.")

    # --- Обработка Ping ---
    @router.message(StateFilter(Advanced.DEVICE_PING))
    async def process_ping_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_host"):
            try:
                await handle_ping_logic(message, state)
            except Exception as e:
                logger.error(f"[PING] Ошибка: {e}", exc_info=True)
                await message.answer("❌ Ошибка при выполнении ping. Попробуйте снова.")
