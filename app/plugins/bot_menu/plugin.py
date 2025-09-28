import os
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional
from importlib import import_module
from aiogram import Router
from app.core.logging_setup import configure_logger
from app.core.plugin_manager.base import PluginBase
from app.core.plugin_manager.descriptors import PluginMetaDescriptor


class BotMenuPlugin(PluginBase):
    """Основной плагин меню бота с поддержкой подплагинов."""

    name = "bot_menu"
    description = "Bot main menu plugin"
    meta = PluginMetaDescriptor(
        name="bot_menu", version="1.0", description="Плагин для основного меню бота"
    )

    def __init__(self):
        self.config: dict[str, Any] = {}
        self.plugin_dir: Optional[Path] = None
        self.router = Router()
        self.subplugins: list[PluginBase] = []
        self.logger = configure_logger().bind(component=self.__class__.__name__)
        self.caller_module = self._get_caller_module()
        self.logger.debug(f"[{self.name}] Caller module: {self.caller_module}")

    def init(self, settings: dict) -> None:
        """Инициализация плагина и загрузка подплагинов."""
        # Определяем рабочую директорию плагина
        self.plugin_dir = self._resolve_plugin_dir(settings)
        self._load_config()
        self._load_subplugins()
        self.logger.info(f"[{self.name}] Инициализация завершена в {self.caller_module}")

    def _resolve_plugin_dir(self, settings: Any) -> Path:
        """Определяет директорию плагина из настроек или по умолчанию."""
        if isinstance(settings, dict) and settings.get("plugin_dir"):
            return Path(settings["plugin_dir"])
        return Path(__file__).parent  # <-- директория текущего плагина

    def _load_config(self) -> None:
        """Загрузка конфигурации и обновление meta."""
        if not self.plugin_dir:
            self.logger.warning(f"[{self.name}] plugin_dir is None, конфиг не загружен")
            return

        config_path = self.plugin_dir / "config.toml"
        if not config_path.exists():
            self.logger.warning(f"[{self.name}] Config not found: {config_path}")
            return

        try:
            with open(config_path, "rb") as f:
                self.config = tomllib.load(f)
            self.logger.debug(f"[{self.name}] Config loaded: {self.config}")
        except Exception as e:
            self.logger.error(f"[{self.name}] Failed to load config: {e}")
            return

        self._update_meta_from_config()

    def _update_meta_from_config(self) -> None:
        """Обновление meta-данных из TOML."""
        for key in ("name", "version", "description"):
            if key in self.config:
                setattr(self.meta, key, self.config[key])

    def _load_subplugins(self) -> None:
        """Загрузка всех подплагинов из поддиректорий."""
        if not self.plugin_dir:
            self.logger.warning(f"[{self.name}] plugin_dir is None, подплагины не загружены")
            return

        self.subplugins.clear()
        for subdir in self.plugin_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("_"):
                self._load_subplugin(subdir)

    def _load_subplugin(self, subdir: Path) -> None:
        plugin_file = subdir / "plugin.py"
        if not plugin_file.exists():
            return

        try:
            # всегда считаем путь относительно папки `app`
            app_root = Path(__file__).parents[2]  # <-- здесь до `app`
            rel_path = subdir.relative_to(app_root)
            module_path = f"app.{str(rel_path).replace(os.sep, '.')}.plugin"

            self.logger.debug(f"[{self.name}] Загружаю подплагин {module_path}")
            module = import_module(module_path)

            plugin_factory = getattr(module, "get_plugin", None)
            if not callable(plugin_factory):
                self.logger.warning(f"[{self.name}] get_plugin() not найден в {module_path}")
                return

            plugin: PluginBase = plugin_factory()
            plugin.init(self.config.get(plugin.name, {}))
            self.subplugins.append(plugin)

            if hasattr(plugin, "router") and isinstance(plugin.router, Router):
                self.router.include_router(plugin.router)

            self.logger.info(f"[{self.name}] ✅ Loaded subplugin: {plugin.name}")

        except Exception as e:
            self.logger.exception(f"[{self.name}] ❌ Ошибка загрузки подплагина {subdir.name}: {e}")

    def extend_main_menu(self, is_admin: bool = False) -> list[Any]:
        """Агрегация пунктов меню из подплагинов."""
        buttons = []
        for plugin in self.subplugins:
            if hasattr(plugin, "extend_main_menu"):
                try:
                    buttons.extend(plugin.extend_main_menu(is_admin))
                except Exception as e:
                    self._log_plugin_error(plugin.name, "extend_main_menu", e)
        return buttons

    def register_aiogram(self, dp: Router) -> None:
        """Регистрация маршрутов aiogram."""
        dp.include_router(self.router)
        for plugin in self.subplugins:
            for method in ("register_handlers", "register_callbacks", "register_inline_query"):
                self._safe_call(plugin, method, dp)

    def _safe_call(self, plugin: PluginBase, method: str, *args: Any) -> None:
        if hasattr(plugin, method):
            try:
                getattr(plugin, method)(*args)
                self.logger.debug(f"[{plugin.name}] {method} registered")
            except Exception as e:
                self._log_plugin_error(plugin.name, method, e)

    def _log_plugin_error(self, plugin_name: str, method: str, error: Exception) -> None:
        self.logger.warning(f"[{plugin_name}] Error in {method}: {error}")

    def execute(self, **kwargs) -> None:
        self.logger.debug(f"[{self.name}] execute called with: {kwargs}")

    def shutdown(self) -> None:
        self.logger.info(f"[{self.name}] Plugin shutdown")

    def _get_caller_module(self) -> str:
        """Определяет модуль, откуда была вызвана инициализация плагина."""
        import inspect
        for frame_info in inspect.stack():
            module = inspect.getmodule(frame_info.frame)
            if module and module.__name__ != __name__:
                return module.__name__
        return "unknown"


def get_plugin() -> BotMenuPlugin:
    return BotMenuPlugin()
