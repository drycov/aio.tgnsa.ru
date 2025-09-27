from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from .menu_label import DutyMenuLabels
from app.bot.constants.labels import MenuLabels as CoreMenuLabels



def get_menu_buttons(is_admin: bool = False) -> list:
    return [KeyboardButton(text=DutyMenuLabels.MAIN.value)]




def build_duty_menu(section: str = "main") -> ReplyKeyboardMarkup:
    from .menu_label import DutyMenuLabels, DUTY_MENU_STRUCTURE

    labels = DUTY_MENU_STRUCTURE.get(section, [])
    buttons = [[KeyboardButton(text=str(label))] for label in labels]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)