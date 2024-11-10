from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.constants import MenuLabels
from app.constants.states import AdvancedCommands
from app.keyboards import advanced_keyboard
from app.utils import StateManager

router = Router()


# Обработчики команд
@router.message(F.text == MenuLabels.ADVANCED.value)
async def advanced_menu(message: Message, state: FSMContext):
    display_data = {"text": MenuLabels.ADVANCED.value, "reply_markup": advanced_keyboard}
    await StateManager.set_state_with_previous(state, AdvancedCommands.MENU, display_data)
    await message.answer(**display_data)


# #
# # @router.message(F.text == MenuLabels.CIDR_CALC.value)
# # async def cidr_calc_command(message: Message, state: FSMContext):
# #     display_data = {"text": "CIDR калькулятор готов к работе."}
# #     await StateManager.set_state_with_previous(state, AdvancedCommands.CIDR_CALCULATOR, display_data)
# #     await message.answer(**display_data)
#
# @router.message(F.text == MenuLabels.CIDR_CALC.value)
# async def cidr_calc_command(message: Message, state: FSMContext):
#     display_data = {"text": "Введите IP-адрес сети (в формате CIDR):"}
#
#     # Установка состояния с текущей командой и сохранение предыдущего состояния
#     await StateManager.set_state_with_previous(state, AdvancedCommands.CIDR_CALCULATOR, display_data)
#
#     # Отправка сообщения о готовности к работе
#     # Ожидание ввода пользователя
#     # Сохранение состояния ожидания IP-адреса
#     await message.answer(**display_data, reply_markup=ReplyKeyboardRemove())
#     await state.update_data(waiting_for_subnet=True)


@router.message(F.text == MenuLabels.P2P_CALC.value)
async def p2p_calc_command(message: Message, state: FSMContext):
    display_data = {"text": "Калькулятор P2P запущен."}
    await StateManager.set_state_with_previous(state, AdvancedCommands.P2P_CALCULATOR, display_data)
    await message.answer(**display_data)


@router.message(F.text == MenuLabels.PING_DEVICE.value)
async def cidr_calc_command(message: Message, state: FSMContext):
    display_data = {"text": "Ping  готов к работе."}
    await StateManager.set_state_with_previous(state, AdvancedCommands.DEVICE_PING, display_data)
    await message.answer(**display_data)


@router.message(F.text == MenuLabels.MASS_INCIDENT_ALERT.value)
async def p2p_calc_command(message: Message, state: FSMContext):
    display_data = {"text": "Массовый инцидент запущен."}
    await StateManager.set_state_with_previous(state, AdvancedCommands.MASS_INCIDENT, display_data)
    await message.answer(**display_data)
