from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
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
