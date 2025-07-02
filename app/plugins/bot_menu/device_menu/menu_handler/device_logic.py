import inspect
from app.bot.fsm.state_manager import StateManager
from aiogram.types import Message, ReplyKeyboardRemove
from app.core.config import logger
import asyncio
from aiogram.fsm.context import FSMContext
from app.bot.keyboards.base import in_back_keyboard

from app.core.utils.device_utils import DeviceUtils
from app.core.utils.network_utils import NetworkUtils
from app.core.utils.snmp_community_scanner import SNMPCommunityScanner

from ..constants.states import DeviceCommands
from ..constants.menu import get_device_keyboard
from app.core.config import settings


async def handle_device_status_logic(message: Message, state: FSMContext):
    host = message.text.strip()
    # Проверка, что введённый текст является IP-адресом
    host, error = await NetworkUtils.validate_ip(host)
    logger.debug(f"Проверка IP-адреса: {host}, ошибка: {error}")
    if error:
        await message.answer(error, reply_markup=in_back_keyboard, parse_mode="HTML")
        await state.update_data(waiting_for_ip=False)
        return
    logger.info(
        f"[device_status] Запрошен статус устройства: user_id={message.from_user.id}, host={host}"
    )
    # Проверка доступности устройства
    is_alive = await NetworkUtils.is_alive(host)
    if not is_alive:
        await message.answer(
            f"⚠️ <b>Устройство <code>{host}</code> недоступно</b>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )
        await state.update_data(waiting_for_ip=False)
        return
    # Если устройство доступно, продолжаем обработку

    # Получение SNMP-сообщества
    scanner = SNMPCommunityScanner(
        target_ip=host,
        communities=settings.net.SNMP_RO,  # Используем список SNMP-сообществ
    )
    logger.debug(f"Проверка SNMP-сообществ для {host}: {settings.net.SNMP_RO}")
    # Асинхронный поиск валидного сообщества
    logger.debug(f"🔍 Ищем валидное SNMP-сообщество для {host}...")
    valid = await scanner.find_valid_community()
    logger.debug(f"✅ Результат: {valid}" if valid else "❌ Ни одна строка не подошла")
    if not valid:
        await message.answer(
            f"⚠️ <b>Не удалось найти SNMP-сообщество для устройства <code>{host}</code></b>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )
        await state.update_data(waiting_for_ip=False)
        return
    await state.update_data(host=host, snmp_community=valid, is_alive=is_alive)

    display_data = {
        "text": f"🔍 <b>Проверка статуса устройства <code>{host}</code></b>",
        "reply_markup": ReplyKeyboardRemove(),
    }
    await StateManager.set_state_with_history(
        state, DeviceCommands.CHECK_STATUS, display_data
    )
    # if_name = await DeviceUtils.get_interface_range(str(host), valid)
    # if_index = await DeviceUtils.get_if_index_range(str(host), valid)
    # logger.info(if_name)
    # logger.info(if_index)

    # interface_map = dict(zip(if_index, if_name))
    # logger.debug(f"Сопоставление интерфейсов: {interface_map}")
    device_info = await DeviceUtils.get_basic_info(str(host), valid)
    if not device_info:
        logger.error(
            f"[{inspect.currentframe().f_code.co_name}] Не удалось получить базовую информацию об устройстве {host}"
        )
        await message.answer(
            f"⚠️ <b>Не удалось получить базовую информацию об устройстве <code>{host}</code></b>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )
        await state.update_data(waiting_for_ip=False)
        return
    logger.info(
        f"[{inspect.currentframe().f_code.co_name}] Получена базовая информация: {device_info}"
    )

    # Запуск асинхронной функции для получения интерфейсов
    # Отправка сообщения пользователю

    await message.answer(**display_data)  # ✅ именно так
    await state.update_data(waiting_for_ip=False)
    await asyncio.sleep(0.1)  # Эмуляция асинхронной работы, если нужно
    keyboard = get_device_keyboard()
    display_data = {
        "text": f"✅ <b>Статус устройства <code>{host}</code> успешно проверен</b>",
        "reply_markup": keyboard,
    }
    await StateManager.set_state_with_history(state, DeviceCommands.MENU, display_data)
    await message.answer(**display_data)
