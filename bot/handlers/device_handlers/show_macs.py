
import json
from aiogram import Router, F, types

from bot.constants.menu_labels import MenuLabels
from bot.constants.regexp import RegExpUtils
from bot.utils import MACVendorLookup
from bot.utils.helper_functions import HelperFunctions
from ertm.ertm import ERTM
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.utils.logger_instance import app_logger
from bot.keyboards.keyboards import in_back_keyboard

router = Router()
regexp = RegExpUtils()
ROWS_PER_PAGE = 20


async def generate_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для пагинации с выделением текущей страницы."""
    keyboard = InlineKeyboardMarkup(row_width=5, inline_keyboard=[])

    # Диапазон страниц для отображения в навигации
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    # Кнопки навигации
    navigation_buttons = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}") if page > 1 else None,
        *[
            InlineKeyboardButton(text=str(i), callback_data=f"page_{i}") if i != page
            else InlineKeyboardButton(text=f"⟨ {i} ⟩", callback_data="current_page")
            for i in range(start_page, end_page + 1)
        ],
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"page_{page + 1}") if page < total_pages else None
    ]

    # Фильтрация None и добавление кнопок
    keyboard.inline_keyboard.append([button for button in navigation_buttons if button])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text=MenuLabels.BACK.value, callback_data="back")])
    return keyboard


@router.message(F.text == MenuLabels.DEVICE_MACS.value)
async def get_mac_addresses(message: Message, state: FSMContext):
    """Хэндлер для получения MAC-адресов через SNMP с указанием IP"""
    action = f"{__name__}.get_mac_addresses"
    data = await state.get_data()
    host = data.get('host')
    community = data.get('community')

    await message.answer(f"🔍 Запрашиваю MAC-адреса с устройства <code>{host}</code>...",parse_mode="HTML",)
    app_logger.info(json.dumps({
            "date": HelperFunctions.get_current_date(),
            "action": action,
            "host": host,
            "usser":message.from_user.id
        }))
    try:
        # Вызываем статический метод parse_snmp_mac через имя класса ERTM
        mac_data = await ERTM.parse_snmp_mac(host, community)
        if mac_data is None:
            await message.answer(f"❌ Ошибка SNMP: не удалось получить данные с <code>{host}</code>"            
                                 f"\n<i>Выполнено:  <code>{HelperFunctions.get_current_date()}</code></i>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",)
            return

        result = f"📋 **MAC-адреса с устройства <code>{host}</code>:**\n"

        # Проходим по полученным портам доступа и транкам
        if "access_ports" in mac_data:
            for port, mac in mac_data["access_ports"].items():
                mac_lookup = MACVendorLookup()
                mac_lookup.load_from_file()

                manufacturer = mac_lookup.get_manufacturer(mac)
                result += f"<i>{port}</i> →  <i>{mac}</i>({manufacturer})\n"

        if "trunk_ports" in mac_data:
            for port, macs in mac_data["trunk_ports"].items():
                result += f"<i>{port}</i> →  Всего MAC: <b>{len(macs)}</b> <u>(Транковый порт)</u>\n"

        await message.reply(
            f"MAC-адреса с устройства: <code>{host}</code>\n<pre>{result}</pre>"
            f"\n<i>Выполнено:  <code>{HelperFunctions.get_current_date()}</code></i>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )
    except AttributeError as e:
        HelperFunctions.log_error(action=action, error=e, host=host)
        await message.reply(
            "Ошибка обработки MAC-адресов"
            f"\n<i>Выполнено:  <code>{HelperFunctions.get_current_date()}</code></i>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )

