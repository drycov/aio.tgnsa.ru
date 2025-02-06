from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters.command import CommandObject, Command

from bot.constants import MenuLabels, ERTMManager, RegExpUtils, Messages
from bot.keyboards import ertm_keyboard, in_back_keyboard, in_cancel_button
from bot.utils import MACVendorLookup, StateManager, NetworkUtils, HelperFunctions
from config import Config
from ertm.ertm import ERTM

router = Router()
regexp = RegExpUtils()


# Основное меню ERTM
@router.message(F.text == MenuLabels.ERTM_MENU.value)
async def advanced_menu_command(message: Message, state: FSMContext):
    display_data = {"text": MenuLabels.ERTM_MENU_MESS.value, "reply_markup": ertm_keyboard}
    await StateManager.set_state_with_previous(state, ERTMManager.ERTM_MENU, display_data)
    await message.answer(**display_data)


# Запуск процесса сканирования оборудования
@router.message(F.text == MenuLabels.ERTM_SCAN_EQUIPMENT.value)
async def cidr_calc_command(message: Message, state: FSMContext):
    display_data = {"text": Messages.ENTER_24_SUBNET.value}
    await StateManager.set_state_with_previous(state, ERTMManager.EQ_SCAN, display_data)
    await message.answer(**display_data, reply_markup=ReplyKeyboardRemove())
    await state.update_data(waiting_for_24_subnet=True)


# Обработка ввода подсети
@router.message(F.text, StateFilter(ERTMManager.EQ_SCAN))
async def process_subnet_input(message: Message, state: FSMContext):
    data = await state.get_data()

    # Проверяем флаг ожидания ввода подсети
    if not data.get('waiting_for_24_subnet'):
        await message.reply(Messages.ERROR_24_SUBNET.value, reply_markup=in_cancel_button)
        return

    network = message.text.strip()  # Удаляем лишние пробелы

    # Проверяем формат IP-адреса
    if not regexp.subnet_24_check(network):
        await message.reply(Messages.ERROR_24_SUBNET.value, reply_markup=in_back_keyboard)
        return

    # Выполняем сканирование сети
    try:
        await scan_network_and_reply(message, network, state)
    except Exception as e:
        await message.reply(f"Ошибка при сканировании сети: {str(e)}")
        await state.clear()


async def scan_network_and_reply(message: Message, network: str, state: FSMContext):
    """
    Выполняет сканирование сети и отвечает пользователю.
    """
    current_date = HelperFunctions.get_current_date()
    await message.reply(
        f"Начинаем сканирование подсети {network}...\nОжидайте результатов",
        reply_markup=ReplyKeyboardRemove()
    )
    try:
        devices = await NetworkUtils.subnet_scan_with_info(network, Config.SNMP_COMMUNITIES)

        if not devices:
            await message.reply("Не найдено доступных устройств в указанной подсети.", reply_markup=in_back_keyboard, parse_mode="HTML")
            await state.clear()
            return

        # Формируем ответ пользователю
        display_data = {
            "text": (
                f"Сканирование сети: {network}\n"
                f"Найдено устройств: {len(devices)}\n"
                f"<i>Выполнено: <code>{current_date}</code></i>"
            ),
            "reply_markup": in_back_keyboard,
            
        }
        await message.reply(**display_data, parse_mode="HTML")
        await state.clear()
    except Exception as e:
        await message.reply(f"Ошибка при сканировании сети: {str(e)}")
        await state.clear()

