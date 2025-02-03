from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.constants import MenuLabels

# Клавиатура для админа
device_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MenuLabels.PORT_STATUS.value),
            KeyboardButton(text=MenuLabels.VLAN_LIST.value),
        ],
        [
            KeyboardButton(text=MenuLabels.DDM_INFO.value),
            KeyboardButton(text=MenuLabels.CABLE_LENGTH_MEASURE.value),
        ],
        [KeyboardButton(text=MenuLabels.DEVICE_LLDP.value),
        KeyboardButton(text=MenuLabels.DEVICE_MACS.value),
        ],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # Это позволяет клавиатуре оставаться на экране
)
