from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.constants import RegExpUtils, Messages
from bot.constants.states import AdvancedCommands
from bot.keyboards import in_back_keyboard
from bot.utils import NetworkUtils

router = Router()
regexp = RegExpUtils()


@router.message(F.text, StateFilter(AdvancedCommands.CIDR_CALCULATOR))
async def process_subnet_input(message: Message, state: FSMContext):
    data = await state.get_data()

    # Проверка, находится ли процесс в ожидании ввода IP-адреса
    if data.get('waiting_for_subnet'):
        subnet = message.text.strip()  # Убираем лишние пробелы

        # Проверка формата IP-адреса
        if not regexp.subnet_check(subnet):
            await message.reply(Messages.ERROR_SUBNET.value, reply_markup=in_back_keyboard)
            return

        # Выполнение расчета сети
        cidr_data = NetworkUtils.subnet_calculate(subnet)
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        display_data = {
            "text":
                f"<b>Расчет IP-сети: <code>{subnet}</code></b>\n\n"
                f"<pre>{cidr_data}</pre>\n\n"
                f"<i>Выполнено: <code>{current_date}</code></i>",
            "reply_markup": in_back_keyboard
        }
        await message.reply(**display_data, parse_mode="HTML")
        await state.clear()
