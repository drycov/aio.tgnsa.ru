from datetime import datetime
import logging
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.bot.keyboards.base import in_back_keyboard
from app.core.logging_setup import configure_logger
from app.core.utils.device_utils import DeviceUtils
from app.core.utils.network_utils import NetworkUtils
from app.core.utils.snmp_community_scanner import SNMPCommunityScanner
from app.core.config import settings
from app.core.utils.decorators import log_execution
from app.bot.fsm.state_manager import StateManager

from ..constants.states import DeviceCommands
from ..constants.menu import get_device_keyboard
from ..constants.messages import Messages

logger = configure_logger().bind(component=f"{__name__}")


@log_execution(success_message="Статус устройства проверен")
async def handle_device_status_logic(message: Message, state: FSMContext):
    host = message.text.strip()

    host, error = await NetworkUtils.validate_ip(host)
    logger.debug(f"Проверка IP-адреса: {host}, ошибка: {error}")
    if error:
        await message.answer(error, reply_markup=in_back_keyboard, parse_mode="HTML")
        await state.update_data(waiting_for_ip=False)
        return

    logger.info(f"[device_status] Запрошен статус: user_id={message.from_user.id}, host={host}")

    is_alive, avg_rtt = await NetworkUtils.is_alive(host)
    if not is_alive:
        await message.answer(
            f"⚠️ <b>Устройство <code>{host}</code> недоступно</b>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML"
        )
        await state.update_data(waiting_for_ip=False)
        return

    scanner = SNMPCommunityScanner(target_ip=host, communities=settings.net.snmp_ro)
    logger.info(f"Проверка SNMP-сообществ для {host}: {settings.net.snmp_ro}")
    valid = await scanner.find_valid_community()
    logger.debug(f"✅ SNMP найден: {valid}" if valid else "❌ Ни одно SNMP-сообщество не подошло")

    if not valid:
        await message.answer(
            f"⚠️ <b>SNMP-сообщество для устройства <code>{host}</code> не найдено</b>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML"
        )
        await state.update_data(waiting_for_ip=False)
        return

    await state.update_data(host=host, snmp_community=valid, is_alive=True)

    await message.answer(
        f"🔍 <b>Проверка статуса устройства <code>{host}</code></b>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

    device_info = await DeviceUtils.get_basic_info(str(host), valid)
    if not device_info:
        logger.error(f"[device_status] Не удалось получить базовую информацию о {host}")
        await message.answer(
            f"⚠️ <b>Нет данных об устройстве <code>{host}</code></b>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML"
        )
        await state.update_data(waiting_for_ip=False)
        return

    logger.info(f"[device_status] Базовая информация: {device_info}")

    await state.update_data(
        model=device_info.get("sw_model", "Неизвестная модель"),
        device_data=device_info.get("device_data", {}),
        waiting_for_ip=False
    )

    # Формирование итогового сообщения
    device_info_message = Messages.DEVICE_INFO.value.format(
        host=device_info.get("host", "Неизвестный хост"),
        vendor=device_info.get("vendor", "n/a"),
        sw_sys_name=device_info.get("sw_sys_name", "n/a"),
        sw_model=device_info.get("sw_model", "n/a"),
        sw_up_time=device_info.get("sw_up_time", "n/a"),
        up_time=device_info.get("up_time", "n/a"),
        address=device_info.get("address", "n/a"),
    )

    keyboard = get_device_keyboard()
    formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    display_data = {
        "text": f"<pre>{device_info_message}</pre>\n\n<i>Выполнено: <code>{formatted_date}</code></i>",
        "reply_markup": keyboard,
        "parse_mode": "HTML"
    }

    await StateManager.set_state_with_history(state, DeviceCommands.MENU, display_data)
    await message.answer(**display_data)

@log_execution(success_message="Проверка портов произведена")
async def handle_port_status_logic(message: Message, state: FSMContext):
    data = await state.get_data()

    host: str = data.get("host")
    community: str = data.get("snmp_community")
    model: str = data.get("model")
    device_data = data.get("device_data", {})

    port_if_list = device_data.get("interfaceList")
    port_if_range = device_data.get("interfaceRange")

    if not host or not community:
        await message.answer("Ошибка: недостающие параметры `host` или `community`.")
        return

    # Получение интерфейсного диапазона, если не указан
    if port_if_range == 'auto' or port_if_range is None:
        port_if_range = await DeviceUtils.get_ifIndex(host, community)

    # Получение списка интерфейсов, если не указан
    if port_if_list == 'auto' or port_if_list is None:
        port_if_list = await DeviceUtils.get_ifDescr(host, community)

    try:
        port_status = await DeviceUtils.get_port_status(host, port_if_list, port_if_range, community, model)
    except:
        pass

    logger.info(f"{port_status}" )