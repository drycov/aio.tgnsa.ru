from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def build_auth_keyboard(is_authenticated: bool) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="🔐 Войти" if not is_authenticated else "🚪 Выйти")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


on_enter_keyboard = build_auth_keyboard(False)

# Клавиатура для отправки контакта
send_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.SHARE_CONTACT.value, request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Оставляет клавиатуру видимой
)
send_contact_keyboard.input_field_placeholder = MenuLabels.SHARE_CONTACT.value
