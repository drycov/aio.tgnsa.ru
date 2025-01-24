from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.constants import RegExpUtils, Messages
from bot.constants.states import AdvancedCommands
from bot.keyboards import in_back_keyboard, advanced_keyboard
from bot.utils import NetworkUtils

router = Router()
regexp = RegExpUtils()


@router.message(F.text, StateFilter(AdvancedCommands.P2P_CALCULATOR))
# Обработчик для ввода данных в P2P калькуляторе
async def process_p2p_input(message: Message, state: FSMContext):
    data = await state.get_data()

    # Проверка, находится ли процесс в ожидании ввода IP-адреса
    if data.get('waiting_for_subnet'):
        subnet = message.text.strip()  # Убираем лишние пробелы

        # Проверка формата IP-адреса
        if not regexp.p2p_check(subnet):
            await message.reply(Messages.ERROR_P2P.value, reply_markup=in_back_keyboard)
            return

        # Выполнение расчета P2P-пары
        p2p_data = NetworkUtils.p2p_calculate(subnet)
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Отправка результата пользователю
        await message.reply(
            f"<b>Расчет P2P-пары: <code>{subnet}</code></b>\n\n"
            f"{p2p_data}\n\n"
            f"<i>Выполнено: <code>{current_date}</code></i>",
            reply_markup=advanced_keyboard,
            parse_mode="HTML"
        )

        # Сброс состояния после выполнения
        await state.clear()
