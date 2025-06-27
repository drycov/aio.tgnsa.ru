from venv import logger
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.constants.labels import MenuLabels
from app.plugins.manager import PluginManager


from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.core.utils.decorators import add_buttons_to_section, chunk_buttons


def generate_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    sections = {
        "main": [
            [],  # одна строка, одна кнопка
        ],
        "ext": [[]],
        "profile": [
            [KeyboardButton(text=MenuLabels.USER_PROFILE.value)],
        ],
        "exit": [
            [KeyboardButton(text=MenuLabels.EXIT.value)],
        ],
        "admin": [
            [KeyboardButton(text=MenuLabels.ADMIN_PANEL.value)] if is_admin else [],
        ],
    }

    pm = PluginManager.get_instance()
    if pm:
        for plugin in pm.plugins.values():
            if hasattr(plugin, "extend_main_menu"):
                try:
                    buttons = plugin.extend_main_menu(is_admin=is_admin)
                    if buttons:
                        if not isinstance(buttons, list):
                            buttons = [buttons]
                        section = getattr(plugin, "menu_section", "main")
                        add_buttons_to_section(
                            sections, section, buttons, max_per_row=2
                        )
                except Exception as e:
                    logger.warning(f"[{plugin.name}] Ошибка при добавлении кнопок: {e}")
    else:
        logger.warning("PluginManager instance is not initialized")

    keyboard_rows = []
    for section_name in ["main", "admin", "profile", "exit"]:
        rows = [row for row in sections.get(section_name, []) if row]
        keyboard_rows.extend(rows)

    return ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        is_persistent=True,
        resize_keyboard=True,
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
        # <- рекомендуется вынести в Enum
        [KeyboardButton(text=MenuLabels.SYSTEM_STATUS.value)],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Администрирование",
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
        input_field_placeholder="Диагностика системы",
    )
