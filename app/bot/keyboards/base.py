from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.bot.constants.labels import MenuLabels
from app.bot.constants.positions import POSITIONS_BY_DEPARTMENT


def build_auth_keyboard(is_authenticated: bool) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚪 Выйти" if is_authenticated else "🔐 Войти")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Действие",
    )


on_enter_keyboard = build_auth_keyboard(False)

# Клавиатура для отправки контакта
send_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.SHARE_CONTACT.value, request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,  # Оставляет клавиатуру видимой
)
send_contact_keyboard.input_field_placeholder = MenuLabels.SHARE_CONTACT.value

send_confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
    ],
)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, Union


def generate_confirm_keyboard(
    action: str,
    payload: Union[int, str],
    confirm_label: str = "✅ Подтвердить",
    cancel_label: str = "❌ Отклонить",
    confirm_suffix: str = "confirm",
    cancel_suffix: str = "cancel",
) -> InlineKeyboardMarkup:
    """
    Генерация универсальной клавиатуры подтверждения.

    :param action: Префикс действия, например 'registration', 'admin', 'delete_user'
    :param payload: Дополнительные данные (user_id, объект и т.д.)
    :param confirm_label: Текст кнопки подтверждения
    :param cancel_label: Текст кнопки отмены
    :param confirm_suffix: Суффикс действия подтверждения
    :param cancel_suffix: Суффикс действия отмены
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=confirm_label,
                    callback_data=f"{action}:{confirm_suffix}:{payload}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=cancel_label,
                    callback_data=f"{action}:{cancel_suffix}:{payload}",
                )
            ],
        ]
    )


on_enter_keyboard = build_auth_keyboard(False)


def generate_department_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"department:{name}")]
            for name in POSITIONS_BY_DEPARTMENT.keys()
        ]
    )
    return keyboard


def generate_position_keyboard(department: str) -> InlineKeyboardMarkup:
    department = department.upper()
    positions = POSITIONS_BY_DEPARTMENT.get(department)

    if not positions:
        # Fallback: кнопка назад при ошибке
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Неверное направление",
                        callback_data="back_to_departments",
                    )
                ]
            ]
        )

    keyboard_buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"position:{code}")]
        for title, code in positions
    ]

    # Добавляем кнопку "Назад"
    keyboard_buttons.append(
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_departments")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


in_deportament_keyboard = generate_department_keyboard()

# Inline-кнопка "Назад"
in_back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=MenuLabels.BACK.value, callback_data="back")]
    ]
)
