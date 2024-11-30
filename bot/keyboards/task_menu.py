from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.constants import MenuLabels

# Клавиатура для админа
task_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MenuLabels.CREATE_TASK.value),
            # KeyboardButton(text=MenuLabels.MASS_INCIDENT_ALERT.value),
        ],
        [
            KeyboardButton(text=MenuLabels.VIEW_MY_TASKS.value),
            KeyboardButton(text=MenuLabels.VIEW_ASSIGNED_TASKS.value),
        ],
        [
            KeyboardButton(text=MenuLabels.VIEW_ALL_TASKS.value),
            # KeyboardButton(text=MenuLabels.MASS_INCIDENT_ALERT.value),
        ],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Это позволяет клавиатуре оставаться на экране
)
