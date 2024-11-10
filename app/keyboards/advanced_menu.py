from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.constants import MenuLabels

# Клавиатура для админа
advanced_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MenuLabels.CIDR_CALC.value),
            KeyboardButton(text=MenuLabels.P2P_CALC.value),
        ],
        [
            KeyboardButton(text=MenuLabels.PING_DEVICE.value),
            # KeyboardButton(text=MenuLabels.MASS_INCIDENT_ALERT.value),
        ],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Это позволяет клавиатуре оставаться на экране
)
