from typing import Union, List, Tuple
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from app.bot.constants.labels import MenuLabels
from app.bot.constants.positions import POSITIONS_BY_DEPARTMENT

logger = logging.getLogger(__name__)


# 🔧 Универсальный хелпер для callback_data
def cb(action: str, *parts: Union[str, int]) -> str:
    return ":".join([action, *(map(str, parts) if parts else [])])


# 🔑 Auth
def build_auth_keyboard(is_authenticated: bool) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MenuLabels.ENTER.value if not is_authenticated else MenuLabels.EXIT.value)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Действие",
    )


# 📱 Контакт
def build_send_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MenuLabels.SHARE_CONTACT.value, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=MenuLabels.SHARE_CONTACT.value,
    )


# ✅/❌ Confirm
def generate_confirm_keyboard(action: str, payload: Union[int, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=cb(action, "confirm", payload))],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=cb(action, "cancel", payload))],
        ]
    )


# 🏢 Departments
def generate_department_keyboard(prefix: str = "department") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=cb(prefix, name))]
            for name in POSITIONS_BY_DEPARTMENT.keys()
        ]
    )


# 👔 Positions
def generate_position_keyboard(department: str, prefix: str = "position") -> InlineKeyboardMarkup:
    positions: List[Tuple[str, str]] = POSITIONS_BY_DEPARTMENT.get(department.upper(), [])

    if not positions:
        logger.warning(f"Department not found: {department}")
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Неверное направление", callback_data=cb("back", "departments"))]]
        )

    keyboard_buttons = [
        [InlineKeyboardButton(text=title, callback_data=cb(prefix, code))] for title, code in positions
    ]
    keyboard_buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=cb("back", "departments"))])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


# 🔙 Back
def build_back_keyboard(callback: str = "back", label: str = "⬅ Назад") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=cb(callback))]]
    )


in_back_keyboard = build_back_keyboard()
