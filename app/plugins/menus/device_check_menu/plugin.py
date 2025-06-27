from typing import List
from aiogram.types import KeyboardButton
from aiogram import Router
from app.plugins.base import Plugin
from .menu import get_menu_buttons
from .handlers import register_handlers


class AdvancedMenuPlugin(Plugin):
    name = "advanced_menu"
    description = "Расширенное меню"
    menu_section = "main"

    def __init__(self):
        self.router = Router()

    def init(self, config: dict | None = None) -> None:
        self._config = config or {}
        # logger.info(f"[{self.name}] Инициализация с конфигом: {self._config}")

    def extend_main_menu(self, is_admin: bool = False) -> List[KeyboardButton]:
        return get_menu_buttons(is_admin=is_admin)

    def register_handlers(self, dp_or_router) -> None:
        register_handlers(dp_or_router)

    # def register_inline_query(self, dp_or_router) -> None:
    #     register_inline_query(dp_or_router)

    # Если будут callback-кнопки — можно добавить:
    # def register_callbacks(self, dp_or_router) -> None:
    #     register_callbacks(dp_or_router)


def get_plugin() -> AdvancedMenuPlugin:
    return AdvancedMenuPlugin()
