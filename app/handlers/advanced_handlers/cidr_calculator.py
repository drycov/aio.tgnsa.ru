from aiogram import types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from datetime import datetime

from app.constants import RegExpUtils, Messages, MenuLabels
from app.constants.states import AdvancedCommands
from app.keyboards import in_back_keyboard
from app.utils import StateManager, NetworkUtils

router = Router()
regexp = RegExpUtils()

@router.message(F.text == MenuLabels.CIDR_CALC.value)
async def cidr_calc_command(message: Message, state: FSMContext):
    display_data = {"text": "Введите IP-адрес сети (в формате CIDR):"}

    # Установка состояния с текущей командой и сохранение предыдущего состояния
    await StateManager.set_state_with_previous(state, AdvancedCommands.CIDR_CALCULATOR, display_data)

    # Отправка сообщения о готовности к работе и удаление клавиатуры
    await message.answer(**display_data, reply_markup=ReplyKeyboardRemove())
    await state.update_data(waiting_for_subnet=True)


@router.message(F.text, StateFilter(AdvancedCommands.CIDR_CALCULATOR))
async def process_subnet_input(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get('waiting_for_subnet'):
        subnet = message.text.strip()  # Убираем лишние пробелы

        # Проверка корректности IP-адреса
        if not regexp.subnet_check(subnet):
            # Сообщение об ошибке, если IP-адрес некорректен
            await message.reply(Messages.ERROR_SUBNET.value, reply_markup=in_back_keyboard)
            return

        # Расчет сети
        cidrData = NetworkUtils.subnet_calculate(subnet)
        currentDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ответ пользователю с результатом расчета
        await message.answer(
            f"<b>Расчет IP-сети: <code>{subnet}</code></b>\n\n<pre>{cidrData}</pre>\n\n<i>Выполнено: <code>{currentDate}</code></i>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML"
        )

        # Сброс состояния и флага ожидания
        await state.update_data(waiting_for_subnet=False)
        await state.clear()
