from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.constants import MenuLabels, Messages
from bot.constants.states import AdvancedCommands
from bot.keyboards import advanced_keyboard
from bot.utils import StateManager

router = Router()


# Обработчик для команды "Расширенное меню"
@router.message(F.text == MenuLabels.ADVANCED.value)
async def advanced_menu_command(message: Message, state: FSMContext):
    display_data = {"text": MenuLabels.ADVANCED.value, "reply_markup": advanced_keyboard}
    await StateManager.set_state_with_previous(state, AdvancedCommands.MENU, display_data)
    await message.answer(**display_data)


# Обработчик для команды "CIDR калькулятор"
@router.message(F.text == MenuLabels.CIDR_CALC.value)
async def cidr_calc_command(message: Message, state: FSMContext):
    display_data = {"text": Messages.ENTER_SUBNET.value}
    await StateManager.set_state_with_previous(state, AdvancedCommands.CIDR_CALCULATOR, display_data)
    await message.answer(**display_data, reply_markup=ReplyKeyboardRemove())
    await state.update_data(waiting_for_subnet=True)


# Обработчик для команды "P2P калькулятор"
@router.message(F.text == MenuLabels.P2P_CALC.value)
async def p2p_calc_command(message: Message, state: FSMContext):
    display_data = {"text": Messages.ENTER_SUBNET_P2P.value}
    await StateManager.set_state_with_previous(state, AdvancedCommands.P2P_CALCULATOR, display_data)
    await message.answer(**display_data, reply_markup=ReplyKeyboardRemove())
    await state.update_data(waiting_for_subnet=True)


# Обработчик для команды "Ping устройства"
@router.message(F.text == MenuLabels.PING_DEVICE.value)
async def ping_device_command(message: Message, state: FSMContext):
    display_data = {"text": Messages.ENTER_IP.value}
    await StateManager.set_state_with_previous(state, AdvancedCommands.DEVICE_PING, display_data)
    await message.answer(**display_data, reply_markup=ReplyKeyboardRemove())
    await state.update_data(waiting_for_host=True)


# Обработчик для команды "Массовый инцидент"
@router.message(F.text == MenuLabels.MASS_INCIDENT_ALERT.value)
async def mass_incident_command(message: Message, state: FSMContext):
    display_data = {"text": "Массовый инцидент запущен."}
    await StateManager.set_state_with_previous(state, AdvancedCommands.MASS_INCIDENT, display_data)
    await message.answer(**display_data)
