from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from .menu_label import MenuLabels
from app.bot.constants.labels import MenuLabels as CoreMenuLabels


def get_menu_buttons(is_admin: bool = False) -> list:
    return [KeyboardButton(text=MenuLabels.ADVANCED.value)]


def get_advanced_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Генератор клавиатуры для расширенного меню.
    При необходимости, может быть расширен логикой is_admin.
    """
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.CIDR_CALC.value),
            KeyboardButton(text=MenuLabels.P2P_CALC.value),
        ],
        [
            KeyboardButton(text=MenuLabels.PING_DEVICE.value),
            KeyboardButton(text=MenuLabels.TRACEROUTE.value),
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
