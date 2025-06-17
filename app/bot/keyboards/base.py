from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.constants.labels import MenuLabels


def build_auth_keyboard(is_authenticated: bool) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="🚪 Выйти" if is_authenticated else "🔐 Войти")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


on_enter_keyboard = build_auth_keyboard(False)

# Клавиатура для отправки контакта
send_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.SHARE_CONTACT.value,
                        request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Оставляет клавиатуру видимой
)
send_contact_keyboard.input_field_placeholder = MenuLabels.SHARE_CONTACT.value
