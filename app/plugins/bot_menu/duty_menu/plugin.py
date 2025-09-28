from pathlib import Path
from typing import List, Dict, Any, Optional
import tomllib

from aiogram import Router
from aiogram.types import KeyboardButton, Message

from app.core.logging_setup import configure_logger
from app.core.plugin_manager.base import PluginBase
from app.core.plugin_manager.descriptors import PluginMetaDescriptor

from app.models.duty import DutyUser, DutyShift, DutyTeam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .constants.menu import get_menu_buttons
from .menu_handler.handlers import register_handlers
from .menu_callback.callbacks import register_callbacks
import inspect


class DutyMenuPlugin(PluginBase):
    name = "duty_menu"
    description = "Дежурства и расписания"
    menu_section = "main"

    meta = PluginMetaDescriptor(
        name="duty_menu",
        version="1.0",
        description="Плагин управления дежурствами",
    )

    def __init__(self):
        self.router = Router()
        self.config: Dict[str, Any] = {}
        self.plugin_dir: Optional[Path] = None
        self.logger = configure_logger().bind(component=f"{__class__.__name__}")
        self.caller_module = self._get_caller_module()

    def init(self, settings: dict) -> None:
        """Инициализация плагина и загрузка конфига."""
        self.plugin_dir = (
            settings.get("plugin_dir")
            if isinstance(settings, dict)
            else getattr(settings, "plugin_dir", Path(__file__).parent)
        )
        self.plugin_dir = self.plugin_dir or Path(__file__).parent
        self._load_config()
        self.logger.info(f"[{self.name}] Плагин инициализирован")

    def _load_config(self) -> None:
        cfg_path = (self.plugin_dir or Path(__file__).parent) / "config.toml"
        if not cfg_path.exists():
            self.logger.warning(f"[{self.name}] Config not found: {cfg_path}")
            return
        try:
            with open(cfg_path, "rb") as f:
                self.config = tomllib.load(f)
            self.logger.debug(f"[{self.name}] Config loaded: {self.config}")
        except Exception as e:
            self.logger.error(f"[{self.name}] Ошибка загрузки конфигурации: {e}")

    def extend_main_menu(self, is_admin: bool = False) -> List[Dict[str, Any]]:
        """Кнопка для вызова расписания дежурств."""
        return get_menu_buttons(is_admin)


    def register_handlers(self, dp_or_router) -> None:
        """Регистрация обработчиков (если есть)."""
        register_handlers(dp_or_router)
        pass
    
    def register_callbacks(self, dp_or_router) -> None:
        """Регистрация callback-обработчиков (если есть)."""
        register_callbacks(dp_or_router)
        pass

    def register_inline_query(self, dp_or_router) -> None:
        """Регистрация inline-обработчиков (если есть)."""
        # register_inline_query(dp_or_router)
        pass
        
    def execute(self, **kwargs: Any) -> None:
        """Обязательный метод из PluginBase (заглушка)."""
        self.logger.debug(f"[{self.name}] execute вызван с аргументами: {kwargs}")

    def get_info(self) -> dict:
        return {
            "name": self.meta.name,
            "version": self.meta.version,
            "description": self.meta.description,
            "config": self.config,
            "menu_section": self.menu_section,
        }

    def shutdown(self) -> None:
        self.logger.info(f"[{self.name}] Плагин завершает работу")

    def _get_caller_module(self) -> str:
        """Определяет модуль вызова плагина."""
        for frame_info in inspect.stack():
            module = inspect.getmodule(frame_info.frame)
            if module and module.__name__ != __name__:
                return module.__name__
        return "unknown"


def get_plugin() -> DutyMenuPlugin:
    return DutyMenuPlugin()
