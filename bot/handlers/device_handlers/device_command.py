from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.constants import MenuLabels, Messages
from bot.constants.states import DeviceCommands
from bot.utils import StateManager

router = Router()


@router.message(F.text == MenuLabels.DEVICE_CHECK.value)
async def process_device_status_input(message: Message, state: FSMContext):
    display_data = {"text": Messages.ENTER_IP.value}
    await StateManager.set_state_with_previous(state, DeviceCommands.CHECK_STATUS, display_data,
                                               "input")
    await message.reply(**display_data, reply_markup=ReplyKeyboardRemove())
    await state.update_data(waiting_for_ip=True)
