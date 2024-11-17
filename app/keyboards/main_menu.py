from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from app.constants import MenuLabels


def generate_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Создает основную клавиатуру с учетом статуса is_admin.
    Если пользователь админ, добавляются дополнительные кнопки.
    """
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.DEVICE_CHECK.value),
            KeyboardButton(text=MenuLabels.ADVANCED.value),
        ],
        [KeyboardButton(text=MenuLabels.TASK_MANAGER.value),
         KeyboardButton(text=MenuLabels.USER_PROFILE.value),
         ],
        [KeyboardButton(text=MenuLabels.EXIT.value)],
    ]

    if is_admin:
        keyboard.insert(1, [KeyboardButton(text=MenuLabels.ADMIN_PANEL.value)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def admin_menu() -> ReplyKeyboardMarkup:
    """Создаем клавиатуру для админов"""
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.VIEW_USERS.value),
            KeyboardButton(text=MenuLabels.SEND_BROADCAST.value),
        ],
        [KeyboardButton(text=MenuLabels.SYSTEM_SETTINGS.value)],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# Клавиатура подтверждения действий
confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.USER_APPROVE.value), KeyboardButton(text=MenuLabels.USER_REJECT.value)]
    ],
    resize_keyboard=True
)

# Инлайн-клавиатура подтверждения
confirm_keyboard_inl = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=MenuLabels.USER_APPROVE.value, callback_data="approve_user"),
        InlineKeyboardButton(text=MenuLabels.USER_REJECT.value, callback_data="reject_user")
    ]
])
