from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from app.constants import MenuLabels

# Клавиатура для кнопки входа
on_enter_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.ENTER.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Оставляет клавиатуру видимой
)
on_enter_keyboard.input_field_placeholder = MenuLabels.ENTER.value

# Inline-кнопка "Назад"
in_back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=MenuLabels.BACK.value, callback_data="back")]
    ]
)

priority_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Low", callback_data="priority_low"),
     InlineKeyboardButton(text="Medium", callback_data="priority_medium"),
     InlineKeyboardButton(text="High", callback_data="priority_high")]
])

# Клавиатура для отправки контакта
send_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.SHARE_CONTACT.value, request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Оставляет клавиатуру видимой
)
send_contact_keyboard.input_field_placeholder = MenuLabels.SHARE_CONTACT.value


# Inline-кнопка для подтверждения пользователя
def verify_user_keyboard(tg_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{MenuLabels.USER_ALLOW.value} {tg_id}", callback_data=f"add_{tg_id}")]
        ]
    )
