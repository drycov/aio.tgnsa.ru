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
    handle_traceroute_logic
)

import logging

logger = configure_logger().bind(component=f"{__name__}")

def register_handlers(router: Router):
    @router.message(F.text == MenuLabels.ADVANCED.value)
    @safe_delete_message
    async def advanced_menu_handler(message: Message, state: FSMContext):
        logger.info(
            f"[advanced_menu] Открыто дополнительное меню: user_id={message.from_user.id}"
        )

        # Пример определения прав администратора (зависит от вашей реализации)
        user_data = await state.get_data()
        is_admin = user_data.get("is_admin", False)

        # Обновление состояния
        await state.update_data(opened_advanced=True)

        # Получение клавиатуры и отображение меню
        keyboard = get_advanced_keyboard(is_admin)
        display_data = {"text": MenuLabels.ADVANCED.value, "reply_markup": keyboard}
        await StateManager.set_state_with_history(state, Advanced.MENU, display_data)
        await message.answer(**display_data)

    # Обработчик для команды "CIDR калькулятор"
    @router.message(F.text == MenuLabels.CIDR_CALC.value)
    async def cidr_calc_command(message: Message, state: FSMContext):
        display_data = {"text": Messages.ENTER_SUBNET.value}
        await StateManager.set_state_with_history(
            state, Advanced.CIDR_CALCULATOR, display_data
        )
        await message.answer(
            **display_data,
        )
        await state.update_data(waiting_for_subnet=True)

    # Обработчик для команды "P2P калькулятор"
    @router.message(F.text == MenuLabels.P2P_CALC.value)
    async def p2p_calc_command(message: Message, state: FSMContext):
        display_data = {"text": Messages.ENTER_SUBNET_P2P.value}
        await StateManager.set_state_with_history(
            state, Advanced.P2P_CALCULATOR, display_data
        )
        await message.answer(
            **display_data,
        )
        await state.update_data(waiting_for_subnet=True)

    # Обработчик для команды "Ping устройства"
    @router.message(F.text == MenuLabels.PING_DEVICE.value)
    async def ping_device_command(message: Message, state: FSMContext):
        display_data = {"text": Messages.ENTER_IP.value}
        await StateManager.set_state_with_history(
            state, Advanced.DEVICE_PING, display_data
        )
        await message.answer(
            **display_data,
        )
        await state.update_data(waiting_for_host=True)
    @router.message(F.text == MenuLabels.TRACEROUTE.value)
    async def traceroute_device_command(message: Message, state: FSMContext):
        display_data = {"text": Messages.ENTER_IP.value}
        await StateManager.set_state_with_history(
            state, Advanced.TRACEROUTE, display_data
        )
        await message.answer(
            **display_data,
        )
        await state.update_data(waiting_for_host=True)

    # Обработка CIDR
    @router.message(StateFilter(Advanced.CIDR_CALCULATOR))
    async def process_cidr_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_subnet"):
            await handle_cidr_logic(message, state)

    # Обработка P2P
    @router.message(StateFilter(Advanced.P2P_CALCULATOR))
    async def process_p2p_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_subnet"):
            await handle_p2p_logic(message, state)

    # Обработка Ping
    @router.message(StateFilter(Advanced.DEVICE_PING))
    async def process_ping_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_host"):
            await handle_ping_logic(message, state)
