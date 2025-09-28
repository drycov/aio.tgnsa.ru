from aiogram.types import KeyboardButton
from .labels.menu_label import MenuLabels


def get_menu_buttons(is_admin: bool = False) -> list:
    return [KeyboardButton(text=MenuLabels.DEVICE_CHECK.value)]
