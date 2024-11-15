from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.constants import RegExpUtils, NetworkMessages
from app.constants.states import DeviceCommands
from app.keyboards import in_back_keyboard, device_keyboard
from app.utils import NetworkUtils, SNMPFunctions, StateManager, DeviceUtils
from app.utils.logger_instance import app_logger
from config import Config

router = Router()
regexp = RegExpUtils()


@router.message(F.text, StateFilter(DeviceCommands.CHECK_STATUS))
async def process_host_input(message: Message, state: FSMContext):
    data = await state.get_data()

    # Проверка, ожидается ли ввод IP-адреса
    if data.get('waiting_for_ip'):
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        host = message.text.strip()  # Убираем лишние пробелы

        # Проверка формата IP-адреса
        if not regexp.ip_check(host):
            await message.reply(NetworkMessages.ERROR_IP_MESSAGE.value, reply_markup=in_back_keyboard)
            return

        # Проверка доступности устройства
        is_alive = await NetworkUtils.is_alive(host)
        app_logger.info(f"Проверка доступности устройства: {host}: {is_alive}")
        if is_alive:
            # Проверка доступного SNMP-сообщества
            community = await SNMPFunctions.check_snmp(host, Config.SNMP_COMMUNITIES)
            if community:
                # Сохранение данных в состоянии
                await state.update_data(host=host, community=community)
                await state.update_data(waiting_for_ip=False)
                await message.reply(
                    "Проверка устройства завершена. Ожидайте результатов.",
                    reply_markup=ReplyKeyboardRemove()
                )
                # Получение информации об устройстве
                # Получение информации об устройстве
                device_info = await DeviceUtils.get_basic_info(host, community)

                # Проверка, что device_info не None и содержит необходимые ключи
                if device_info and all(
                        key in device_info for key in ['host', 'sw_sys_name', 'sw_model', 'sw_up_time', 'up_time']):
                    device_info_message = NetworkMessages.DEVICE_INFO.value.format(
                        host=device_info.get('host', 'Неизвестный хост'),
                        sw_sys_name=device_info.get('sw_sys_name', 'Неизвестное имя'),
                        sw_model=device_info.get('sw_model', 'Неизвестная модель'),
                        sw_up_time=device_info.get('sw_up_time', 'Неизвестное время работы системы'),
                        up_time=device_info.get('up_time', 'Неизвестное время работы')
                    )

                    # Обновление состояния с данными устройства
                    await state.update_data(
                        model=device_info.get('sw_model', 'Неизвестная модель'),
                        device_data=device_info.get('device_data', {})
                    )

                    # Подготовка данных для отображения
                    display_data = {
                        "text": f"<pre>{device_info_message}</pre>\n\n"
                                f"<i>Выполнено: <code>{current_date}</code></i>",
                        "reply_markup": device_keyboard
                    }
                else:
                    # Обработка ситуации, когда данные об устройстве отсутствуют или неполные
                    device_info_message = "Информация об устройстве недоступна или неполная."
                    display_data = {
                        "text": f"<pre>{device_info_message}</pre>\n\n"
                                f"<i>Выполнено: <code>{current_date}</code></i>",
                        "reply_markup": in_back_keyboard
                    }

                # Переход в состояние ADMIN_PANEL с отображением данных
                await message.reply(**display_data)
                await StateManager.set_state_with_previous(state, DeviceCommands.MENU, display_data, '')
                await state.update_data(waiting_for_ip=False)
            else:
                # Сообщение, если SNMP-сообщество не найдено
                await message.reply(
                    "Не удалось найти подходящее SNMP-сообщество для устройства.",
                    reply_markup=in_back_keyboard
                )
        else:
            # Сообщение, если устройство недоступно
            await message.reply(
                "Устройство по указанному IP-адресу недоступно.",
                reply_markup=in_back_keyboard
            )
    else:
        # Сообщение, если система не ожидает IP-адреса
        await message.reply(
            "Система не ожидает ввода IP-адреса. Пожалуйста, начните процесс сначала.",
            reply_markup=in_back_keyboard
        )
