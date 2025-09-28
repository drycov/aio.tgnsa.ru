from pathlib import Path
import tomllib
from typing import List, Optional, Dict, Any
from aiogram import Router
from aiogram.types import KeyboardButton

from app.core.logging_setup import configure_logger
from app.core.plugin_manager.base import PluginBase
from app.core.plugin_manager.descriptors import PluginMetaDescriptor

from .menu_handler.handlers import register_handlers
from .constants.menu import get_menu_buttons

import inspect


class DeviceCheckMenuPlugin(PluginBase):
    """Плагин меню проверки устройств в сети."""

    # ========== STATIC META ==========
    name = "device_check_menu"
    description = "Меню проверки устройства"
    menu_section = "main"

    meta = PluginMetaDescriptor(
        name=name,
        version="1.0",
        description=description,
    )

    def __init__(self):
        self.router = Router()
        self.config: Dict[str, Any] = {}
        self.plugin_dir: Optional[Path] = None
        self.logger = configure_logger().bind(component=self.__class__.__name__)
        self.caller_module = self._get_caller_module()
        self.logger.debug(f"[{self.name}] Caller module: {self.caller_module}")

    # ========== LIFECYCLE ==========

    def init(self, settings: dict) -> None:
        """Инициализация плагина."""
        try:
            plugin_dir = (
                settings.get("plugin_dir")
                if isinstance(settings, dict)
                else getattr(settings, "plugin_dir", None)
            )
            self.plugin_dir = plugin_dir or Path(__file__).parent

            self.load_config()
            self.logger.info(
                f"[{self.name}] Плагин инициализирован (caller={self.caller_module})"
            )

        except Exception as e:
            self.logger.exception(f"[{self.name}] Ошибка при инициализации: {e}")
            raise

    def shutdown(self) -> None:
        """Завершение работы плагина."""
        self.logger.info(f"[{self.name}] Плагин остановлен")

    # ========== CONFIG ==========

    def load_config(self, plugin_dir: Optional[Path] = None) -> None:
        """Загрузка конфигурации из TOML-файла и обновление метаинформации."""
        plugin_dir = plugin_dir or self.plugin_dir or Path(__file__).parent
        cfg_path = plugin_dir / "config.toml"

        if not cfg_path.exists():
            self.logger.warning(f"[{self.name}] Конфигурационный файл не найден: {cfg_path}")
            return

        try:
            with open(cfg_path, "rb") as f:
                self.config = tomllib.load(f)
            self.logger.debug(f"[{self.name}] Конфигурация загружена: {self.config}")

            self._update_meta_from_config()
        except Exception as e:
            self.logger.error(f"[{self.name}] Ошибка при загрузке конфигурации: {e}")

    def _update_meta_from_config(self) -> None:
        """Обновление meta-данных плагина из конфига."""
        if not self.config:
            return
        for field in ("name", "version", "description"):
            if field in self.config:
                setattr(self.meta, field, self.config[field])

    # ========== EXTENSIONS ==========

    def extend_main_menu(self, is_admin: bool = False) -> List[KeyboardButton]:
        """Добавление кнопок в основное меню."""
        try:
            return get_menu_buttons()
        except Exception as e:
            self.logger.error(f"[{self.name}] Ошибка в extend_main_menu: {e}")
            return []

    def register_handlers(self, dp_or_router) -> None:
        """Регистрация хендлеров."""
        try:
            register_handlers(dp_or_router)
            self.logger.debug(f"[{self.name}] Handlers зарегистрированы")
        except Exception as e:
            self.logger.error(f"[{self.name}] Ошибка при регистрации handlers: {e}")

    def register_callbacks(self, dp_or_router) -> None:
        """Регистрация callback-хендлеров."""
        # TODO: реализовать при необходимости
        pass

    def register_inline_query(self, dp_or_router) -> None:
        """Регистрация inline query хендлеров."""
        # TODO: реализовать при необходимости
        pass

    def execute(self, **kwargs: Any) -> None:
        """Произвольный вызов плагина (например, тесты или CLI)."""
        self.logger.debug(f"[{self.name}] execute вызван с аргументами: {kwargs}")

    # ========== UTILS ==========

    def get_info(self) -> dict:
        """Возвращает информацию о плагине и его конфиге."""
        return {
            "name": self.meta.name,
            "version": self.meta.version,
            "description": self.meta.description,
            "config": self.config,
        }

    def _get_caller_module(self) -> str:
        """Определяет модуль, откуда была вызвана инициализация плагина."""
        for frame_info in inspect.stack():
            module = inspect.getmodule(frame_info.frame)
            if module and module.__name__ != __name__:
                return module.__name__
        return "unknown"


# --- Factory Methods ---
def get_plugin() -> DeviceCheckMenuPlugin:
    return DeviceCheckMenuPlugin()


def get_plugin_instance() -> DeviceCheckMenuPlugin:
    """Функция для получения экземпляра плагина (совместимость с PluginManager)."""
    return DeviceCheckMenuPlugin()
