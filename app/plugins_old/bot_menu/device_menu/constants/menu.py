from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from .menu_label import MenuLabels
from app.bot.constants.labels import MenuLabels as CoreMenuLabels


def get_menu_buttons() -> list:
    return [KeyboardButton(text=MenuLabels.DEVICE_CHECK.value)]


def get_device_keyboard() -> ReplyKeyboardMarkup:
    """
    Генератор клавиатуры для меню устройства.
    При необходимости, может быть расширен логикой is_admin.
    """
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.PORT_STATUS.value),
            KeyboardButton(text=MenuLabels.VLAN_LIST.value),
        ],
        [
            KeyboardButton(text=MenuLabels.DDM_INFO.value),
            KeyboardButton(text=MenuLabels.CABLE_LENGTH_MEASURE.value),
        ],
        [
            KeyboardButton(text=MenuLabels.DEVICE_LLDP.value),
            KeyboardButton(text=MenuLabels.DEVICE_MACS.value),
        ],
        [KeyboardButton(text=CoreMenuLabels.BACK.value)],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        is_persistent=True,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Инструменты диагностики",
    )


async def generate_pagination_keyboard(
    page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для пагинации с выделением текущей страницы."""
    keyboard = InlineKeyboardMarkup(row_width=5, inline_keyboard=[])

    # Диапазон страниц для отображения в навигации
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    # Кнопки навигации
    navigation_buttons = [
        (
            InlineKeyboardButton(
                text=MenuLabels.PPAGE.value, callback_data=f"page_{page - 1}"
            )
            if page > 1
            else None
        ),
        *[
            (
                InlineKeyboardButton(text=str(i), callback_data=f"page_{i}")
                if i != page
                else InlineKeyboardButton(text=f"⟨ {i} ⟩", callback_data="current_page")
            )
            for i in range(start_page, end_page + 1)
        ],
        (
            InlineKeyboardButton(
                text=MenuLabels.NPAGE.value, callback_data=f"page_{page + 1}"
            )
            if page < total_pages
            else None
        ),
    ]

    # Фильтрация None и добавление кнопок
    keyboard.inline_keyboard.append([button for button in navigation_buttons if button])
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text=CoreMenuLabels.BACK.value, callback_data="back")]
    )
    return keyboard
