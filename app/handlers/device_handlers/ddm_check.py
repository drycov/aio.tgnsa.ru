from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove

from app.constants import MenuLabels
from app.keyboards import in_back_keyboard
from app.utils import HelperFunctions, DeviceUtils

router = Router()

# Максимальное количество строк на одной странице
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


@router.message(F.text == MenuLabels.DDM_INFO.value)
async def ddm_info(message: Message, state: FSMContext):
    """
    Вывод уровня оптического сигнала/ADSL на устройстве через Telegram-бота.
    """
    action = f"{__name__}.ddm_info"
    current_date = HelperFunctions.get_current_date()

    data = await state.get_data()
    host = data.get('host')
    community = data.get('community')
    model = data.get('model')
    device_data = data.get('device_data', {})
    port_if_list = data.get('device_data', {}).get('interfaceList', [])
    port_if_range = data.get('device_data', {}).get('interfaceRange', [])

    await message.reply(
        f"Вывод уровня оптического сигнала/ADSL на устройстве: <code>{host}</code>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

    try:
        ddm_info = await DeviceUtils.get_ddm_info(host, port_if_list, port_if_range, device_data, community)

        await message.reply(
            f"Уровень оптического сигнала/ADSL на устройстве: <code>{host}</code>\n<pre>{ddm_info}</pre>"
            f"\n<i>Выполнено:  <code>{current_date}</code></i>",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )


    except Exception as e:

        HelperFunctions.log_error(action=action, error=e, host=host)
        await message.reply(
            "Ошибка",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )
