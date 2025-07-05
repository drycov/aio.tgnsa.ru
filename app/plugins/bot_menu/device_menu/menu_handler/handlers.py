import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.fsm.state_manager import StateManager
from app.bot.keyboards.base import in_back_keyboard
from app.core.logging_setup import configure_logger
from app.core.utils.decorators import safe_delete_message

from ..constants.menu_label import MenuLabels
from ..constants.messages import Messages
from ..constants.states import DeviceCommands
from .device_logic import handle_device_status_logic

logger = configure_logger().bind(component=f"{__name__}")


def register_handlers(router: Router):

    @router.message(F.text == MenuLabels.DEVICE_CHECK.value)
    @safe_delete_message
    async def process_device_status_input(message: Message, state: FSMContext):
        display_data = {
            "text": Messages.ENTER_IP.value,
            "reply_markup": ReplyKeyboardRemove(),
        }
        await StateManager.set_state_with_history(
            state, DeviceCommands.CHECK_STATUS, display_data
        )

        await message.answer(**display_data)

        await state.update_data(waiting_for_ip=True)

    @router.message(StateFilter(DeviceCommands.CHECK_STATUS))
    async def process_host_input(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get("waiting_for_ip"):
            await handle_device_status_logic(message, state)
        else:
            await message.reply(
                "Система не ожидает ввода IP-адреса. Пожалуйста, начните процесс сначала.",
                reply_markup=in_back_keyboard,
            )
            return
