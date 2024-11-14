from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import RegExpUtils, NetworkMessages
from app.constants.states import AdvancedCommands
from app.keyboards import in_back_keyboard
from app.utils import NetworkUtils

router = Router()
regexp = RegExpUtils()


@router.message(F.text, StateFilter(AdvancedCommands.DEVICE_PING))
# Обработчик для ввода данных в P2P калькуляторе
async def process_ping_node_input(message: Message, state: FSMContext):
    data = await state.get_data()

    # Проверка, находится ли процесс в ожидании ввода IP-адреса
    if data.get('waiting_for_host'):
        host = message.text.strip()  # Убираем лишние пробелы

        # Проверка корректности IP-адреса
        if not regexp.ip_check(host):
            await message.reply(NetworkMessages.ERROR_IP_MESSAGE.value, reply_markup=in_back_keyboard)
            return

        # Выполнение расчета P2P-пары
        ping_data = NetworkUtils.ping_device_log(host)
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Отправка результата пользователю
        await message.reply(
            f"<b>Ping device: <code>{host}</code> log</b>\n\n"
            f"<i>{ping_data}</i>\n\n"
            f"<i>Выполнено: <code>{current_date}</code></i>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML"
        )

        # Сброс состояния после выполнения
        await state.clear()
