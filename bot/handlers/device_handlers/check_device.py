from datetime import datetime
import json

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.bot_instance import ertm
from bot.constants import RegExpUtils, NetworkMessages
from bot.constants.states import DeviceCommands
from bot.keyboards import in_back_keyboard, device_keyboard
from bot.utils import NetworkUtils, SNMPFunctions, StateManager, DeviceUtils
from bot.utils.helper_functions import HelperFunctions
from config import Config

router = Router()
regexp = RegExpUtils()

async def validate_ip(host: str, message: Message) -> bool:
    """Проверка корректности IP-адреса."""
    if not regexp.ip_check(host):
        await message.reply(NetworkMessages.ERROR_IP_MESSAGE.value, reply_markup=in_back_keyboard)
        return False
    return True

async def check_device_availability(host: str, message: Message) -> bool:
    """Проверка доступности устройства по IP."""
    is_alive = await NetworkUtils.is_alive(host)
    if not is_alive:
        await message.reply("Устройство по указанному IP-адресу недоступно.", reply_markup=in_back_keyboard)
    return is_alive

async def get_snmp_community(host: str) -> str:
    """Получение SNMP-сообщества для устройства."""
    return await SNMPFunctions.check_snmp(host, Config.SNMP_COMMUNITIES)

async def process_device_info(host: str, community: str, message: Message, state: FSMContext):
    """Обработка информации об устройстве и обновление состояния."""
    device_info = await DeviceUtils.get_basic_info(host, community)
    if not device_info or not all(key in device_info for key in ['host', 'sw_sys_name', 'sw_model', 'sw_up_time', 'up_time']):
        await message.reply("Информация об устройстве недоступна или неполна.", reply_markup=in_back_keyboard)
        return

    # Добавление устройства в систему
    await ertm.add_device(
        host=host,
        vendor=device_info.get('vendor', 'nAn'),
        sys_name=device_info.get('sw_sys_name', 'nAn'),
        model=device_info.get('sw_model', 'nAn'),
        latitude=device_info.get('latitude', 0),
        longitude=device_info.get('longitude', 0),
        address=device_info.get('address', 'nAn'),
    )

    # Формирование сообщения с информацией об устройстве
    device_info_message = NetworkMessages.DEVICE_INFO.value.format(
        host=device_info.get('host', 'Неизвестный хост'),
        vendor=device_info.get('vendor', 'nAn'),
        sw_sys_name=device_info.get('sw_sys_name', 'Неизвестное имя'),
        sw_model=device_info.get('sw_model', 'Неизвестная модель'),
        sw_up_time=device_info.get('sw_up_time', 'Неизвестное время работы системы'),
        up_time=device_info.get('up_time', 'Неизвестное время работы'),
        address=device_info.get('address', 'Неизвестный адрес'),
    )

    # Обновление состояния с данными устройства
    await state.update_data(
        model=device_info.get('sw_model', 'Неизвестная модель'),
        device_data=device_info.get('device_data', {})
    )

    # Подготовка данных для отображения
    display_data = {
        "text": f"<pre>{device_info_message}</pre>\n\n<i>Выполнено: <code>{HelperFunctions.get_current_date()}</code></i>",
        "reply_markup": device_keyboard
    }

    # Отправка сообщения с информацией об устройстве
    await message.reply(**display_data, parse_mode="HTML")
    await StateManager.set_state_with_previous(state, DeviceCommands.MENU, display_data, '')
    await state.update_data(waiting_for_ip=False)

@router.message(F.text, StateFilter(DeviceCommands.CHECK_STATUS))
async def process_host_input(message: Message, state: FSMContext):
    """Обработка ввода IP-адреса пользователем."""
    data = await state.get_data()
    if not data.get('waiting_for_ip'):
        await message.reply("Система не ожидает ввода IP-адреса. Пожалуйста, начните процесс сначала.", reply_markup=in_back_keyboard)
        return

    host = message.text.strip()
    if not await validate_ip(host, message):
        return

    # Логирование действия
    await HelperFunctions.log_action(f"{__name__}.process_host_input", host, message.from_user.id)

    # Проверка доступности устройства
    if not await check_device_availability(host, message):
        return

    # Получение SNMP-сообщества
    community = await get_snmp_community(host)
    if not community:
        await message.reply("Не удалось найти подходящее SNMP-сообщество для устройства.", reply_markup=in_back_keyboard)
        return

    # Обновление состояния и обработка информации об устройстве
    await state.update_data(host=host, community=community)
    await message.reply("Проверка устройства завершена. Ожидайте результатов.", reply_markup=ReplyKeyboardRemove())
    await process_device_info(host, community, message, state)