from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.bot.constants.labels import MenuLabels


def generate_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Основное меню. Динамически формируется в зависимости от роли пользователя.
    """
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.DEVICE_CHECK.value),
            KeyboardButton(text=MenuLabels.ADVANCED.value),
        ],
        [KeyboardButton(text=MenuLabels.ERTM_MENU.value)],
        [
            KeyboardButton(text=MenuLabels.TASK_MANAGER.value),
            KeyboardButton(text=MenuLabels.USER_PROFILE.value),
        ],
        [KeyboardButton(text=MenuLabels.EXIT.value)],
    ]

    if is_admin:
        keyboard.insert(1, [KeyboardButton(text=MenuLabels.ADMIN_PANEL.value)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие из меню"
    )


def admin_menu() -> ReplyKeyboardMarkup:
    """
    Подменю администратора.
    """
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.VIEW_USERS.value),
            KeyboardButton(text=MenuLabels.SEND_BROADCAST.value),
        ],
        [KeyboardButton(text=MenuLabels.SYSTEM_STATUS.value)],  # <- рекомендуется вынести в Enum
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Администрирование"
    )


def system_info_menu() -> ReplyKeyboardMarkup:
    """
    Подменю состояния системы и диагностики.
    """
    keyboard = [
        [KeyboardButton(text=MenuLabels.SYSTEM_STATUS.value)],
        [
            KeyboardButton(text=MenuLabels.CHECK_COMPONENTS.value),
            KeyboardButton(text=MenuLabels.RESTART_CHECKS.value),
        ],
        [KeyboardButton(text=MenuLabels.GET_LOGS.value)],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Диагностика системы"
    )
