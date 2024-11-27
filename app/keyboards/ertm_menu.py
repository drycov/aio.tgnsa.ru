from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.constants import MenuLabels

# Клавиатура для админа
ertm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MenuLabels.ERTM_ADD_EQUIPMENT.value),
            KeyboardButton(text=MenuLabels.ERTM_LIST_EQUIPMENT.value),
        ],
        [
            KeyboardButton(text=MenuLabels.ERTM_TRACK_EQUIPMENT.value),
            KeyboardButton(text=MenuLabels.ERTM_SCAN_EQUIPMENT.value),
        ],
        [KeyboardButton(text=MenuLabels.ERTM_MANAGE_EQUIPMENT.value)],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Это позволяет клавиатуре оставаться на экране
)
ertm_track_location = ReplyKeyboardMarkup(  # Это позволяет клавиатуре оставаться на экране
    keyboard=[
        [
            KeyboardButton(text="📍 Отправить локацию", request_location=True)
        ], [KeyboardButton(text=MenuLabels.BACK.value)],
    ], resize_keyboard=True,
    one_time_keyboard=False, )
