from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.bot.constants.labels import MenuLabels
from app.core.plugin_manager.manager import PluginManager
from app.core.utils.decorators import add_buttons_to_section

import logging


def generate_main_keyboard(
    is_admin: bool = False, max_per_row: int = 2, logger: logging.Logger | None = None
) -> ReplyKeyboardMarkup:
    logger = logger or logging.getLogger("MainMenu")

    sections: dict[str, list[list[KeyboardButton]]] = {
        "main": [],
        "ext": [],
        "profile": [[KeyboardButton(text=MenuLabels.USER_PROFILE.value)]],
        "exit": [[KeyboardButton(text=MenuLabels.EXIT.value)]],
    }

    if is_admin:
        sections["admin"] = [[KeyboardButton(text=MenuLabels.ADMIN_PANEL.value)]]

    pm = PluginManager.get_instance()
    pm.ensure_ready()  # гарантируем загрузку

    if pm.is_initialized:
        for plugin in pm.all_plugins().values():
            if hasattr(plugin, "extend_main_menu"):
                try:
                    buttons = plugin.extend_main_menu(is_admin=is_admin)
                    if not buttons:
                        continue
                    if not isinstance(buttons, list):
                        buttons = [buttons]

                    section = getattr(plugin, "menu_section", "main")
                    add_buttons_to_section(sections, section, buttons, max_per_row=max_per_row)
                    logger.debug(f"[{plugin.__class__.__name__}] кнопки добавлены в {section}")

                except Exception as e:
                    plugin_name = getattr(getattr(plugin, "meta", None), "name", plugin.__class__.__name__)
                    logger.warning(f"[{plugin_name}] Ошибка при добавлении кнопок: {e}", exc_info=True)
    else:
        logger.warning("PluginManager is not initialized")

    # Собираем клавиатуру
    keyboard_rows = []
    for section in ("main", "admin", "profile", "exit"):
        keyboard_rows.extend([row for row in sections.get(section, []) if row])

    return ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        is_persistent=True,
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MenuLabels.VIEW_USERS.value),
                KeyboardButton(text=MenuLabels.SEND_BROADCAST.value),
            ],
            [KeyboardButton(text=MenuLabels.SYSTEM_STATUS.value)],
            [KeyboardButton(text=MenuLabels.BACK.value)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Администрирование",
    )


def system_info_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MenuLabels.SYSTEM_STATUS.value)],
            [
                KeyboardButton(text=MenuLabels.CHECK_COMPONENTS.value),
                KeyboardButton(text=MenuLabels.RESTART_CHECKS.value),
            ],
            [KeyboardButton(text=MenuLabels.GET_LOGS.value)],
            [KeyboardButton(text=MenuLabels.BACK.value)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Диагностика системы",
    )
