import logging
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from .menu_label import DutyMenuLabels
from app.bot.constants.labels import MenuLabels as CoreMenuLabels

logger = logging.getLogger(__name__)


def get_menu_buttons(is_admin: bool = False) -> list:
    return [KeyboardButton(text=DutyMenuLabels.MAIN.value)]




def build_duty_menu(section: str = "main") -> ReplyKeyboardMarkup:
    from .menu_label import DUTY_MENU_STRUCTURE

    labels = DUTY_MENU_STRUCTURE.get(section)
    if not labels:
        logger.warning(f"[build_duty_menu] Секция {section!r} не найдена, откат к 'main'")
        labels = DUTY_MENU_STRUCTURE.get("main", [])

    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []

    for label in labels:
        row.append(KeyboardButton(text=str(label)))
        if len(row) == 2:  # по 2 кнопки в строке
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )
