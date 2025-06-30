from pathlib import Path
import tomllib
from typing import List, Optional, Dict, Any
from aiogram import Router
from aiogram.types import KeyboardButton

from app.core.plugin_manager.base import PluginBase
from app.core.config import logger
from app.core.plugin_manager.descriptors import PluginMetaDescriptor
import inspect

from .constants.menu import get_menu_buttons
from .menu_handler.handlers import register_handlers

# from .menu_handler.callbacks import register_callbacks
# from .menu_handler.inline import register_inline_query


class AdvancedMenuPlugin(PluginBase):
    name = "advanced_menu"
    description = "Расширенное меню"
    menu_section = "main"

    meta = PluginMetaDescriptor(
        name="advanced_menu",
        version="1.0",
        description="Плагин для расширенного меню бота",
    )

    def __init__(self):
        self.router = Router()
        self.config: Dict[str, Any] = {}
        self.plugin_dir: Optional[Path] = None
        self.logger = logger.bind(component=self.name)
        self.caller_module = self._get_caller_module()
        self.logger.debug(f"[{self.name}] Caller module: {self.caller_module}")

    def init(self, settings: dict) -> None:
        try:
            plugin_dir = (
                settings.get("plugin_dir")
                if isinstance(settings, dict)
                else getattr(settings, "plugin_dir", None)
            )
            self.plugin_dir = plugin_dir or Path(__file__).parent

            self.load_config()

            self.logger.info(
                f"[{self.name}] Плагин инициализирован  из {self.caller_module}"
            )

        except Exception as e:
            self.logger.exception(f"[{self.name}] Ошибка при инициализации: {e}")
            raise e

    def load_config(self) -> None:
        """Загрузка конфигурации из config.toml и обновление meta."""
        plugin_dir = self.plugin_dir or Path(__file__).parent
        cfg_path = plugin_dir / "config.toml"

        if not cfg_path.exists():
            self.logger.warning(f"[{self.name}] Config file not found: {cfg_path}")
            return

        try:
            with open(cfg_path, "rb") as f:
                self.config = tomllib.load(f)

            self.logger.debug(f"[{self.name}] Конфигурация загружена: {self.config}")
            self._update_meta_from_config()

        except Exception as e:
            self.logger.error(f"[{self.name}] Ошибка при загрузке конфигурации: {e}")

    def _update_meta_from_config(self) -> None:
        """Обновление meta-данных плагина из config.toml."""
        if not self.config:
            return
        for key in ("name", "version", "description"):
            if key in self.config:
                setattr(self.meta, key, self.config[key])

    def extend_main_menu(self, is_admin: bool = False) -> List[KeyboardButton]:
        """Расширение основного меню (опционально)."""
        return get_menu_buttons(is_admin)

    def register_handlers(self, dp_or_router) -> None:
        """Регистрация обработчиков (если есть)."""
        register_handlers(dp_or_router)
        pass

    def register_callbacks(self, dp_or_router) -> None:
        """Регистрация callback-обработчиков (если есть)."""
        # register_callbacks(dp_or_router)
        pass

    def register_inline_query(self, dp_or_router) -> None:
        """Регистрация inline-обработчиков (если есть)."""
        # register_inline_query(dp_or_router)
        pass

    def execute(self, **kwargs: Any) -> None:
        self.logger.debug(f"[{self.name}] execute() вызван с аргументами: {kwargs}")

    def get_info(self) -> dict:
        return {
            "name": self.meta.name,
            "version": self.meta.version,
            "description": self.meta.description,
            "config": self.config,
        }

    def shutdown(self) -> None:
        self.logger.info(f"[{self.name}] Плагин завершает работу")

    def _get_caller_module(self) -> str:
        """Определяет модуль, откуда была вызвана инициализация плагина."""
        import inspect

        for frame_info in inspect.stack():
            module = inspect.getmodule(frame_info.frame)
            if module and module.__name__ != __name__:
                return module.__name__
        return "unknown"


def get_plugin() -> AdvancedMenuPlugin:
    return AdvancedMenuPlugin()


# This function is used to retrieve the plugin instance.
# It allows the plugin manager to access the plugin without directly importing it.
def get_plugin_instance() -> AdvancedMenuPlugin:
    """Функция для получения экземпляра плагина."""
    return AdvancedMenuPlugin()
