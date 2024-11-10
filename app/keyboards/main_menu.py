from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from app.constants import MenuLabels

# Клавиатура для админа
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MenuLabels.DEVICE_CHECK.value),
            KeyboardButton(text=MenuLabels.ADVANCED.value),
        ],
        [KeyboardButton(text=MenuLabels.ADMIN_PANEL.value), KeyboardButton(text=MenuLabels.TASK_MANAGER.value)],
        [KeyboardButton(text=MenuLabels.EXIT.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Это позволяет клавиатуре оставаться на экране
)

# Основная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MenuLabels.DEVICE_CHECK.value),
            KeyboardButton(text=MenuLabels.ADVANCED.value),
        ],
        [KeyboardButton(text=MenuLabels.TASK_MANAGER.value)],
        [KeyboardButton(text=MenuLabels.EXIT.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Это также сохраняет клавиатуру на экране
)
confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.USER_APPROVE.value), KeyboardButton(text=MenuLabels.USER_REJECT.value)]
    ],
    resize_keyboard=True
)
# Создание инлайн-клавиатуры
confirm_keyboard_inl = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=MenuLabels.USER_APPROVE.value, callback_data="approve_user"),
        InlineKeyboardButton(text=MenuLabels.USER_REJECT.value, callback_data="reject_user")
    ]
])
