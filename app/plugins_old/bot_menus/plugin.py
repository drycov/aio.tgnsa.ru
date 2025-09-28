from app.plugins_old.base import Plugin
from pathlib import Path
import importlib
from typing import List, Optional, Dict, Any, Callable
from aiogram import Router, Dispatcher
from app.core.config import logger as app_logger
from logging import Logger


class MenusPlugin(Plugin):
    name = "bot_menus"
    description = "Основной плагин для меню, содержит подплагины"
    priority: int = 10

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__()
        self.subplugins: List[Plugin] = []
        self.router = Router()
        self.logger = logger or app_logger
        self.name = getattr(self.__class__, "name", self.__class__.__name__)
        self._config: Dict[str, Any] = {}

        self.logger.info(f"[{self.name}] Plugin initialized")

    def init(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the MenusPlugin and loads subplugins.

        :param config: Configuration dictionary for the plugin and its subplugins.
        """
        self._config = config or {}
        plugins_dir = Path(__file__).parent
        self.subplugins.clear()

        self.logger.debug(f"[{self.name}] Scanning for subplugins in: {plugins_dir}")

        for subfolder in plugins_dir.iterdir():
            if not subfolder.is_dir() or subfolder.name == "__pycache__":
                continue

            plugin_file = subfolder / "plugin.py"
            if not plugin_file.exists():
                continue

            module_name = f"{self.__module__.rsplit('.', 1)[0]}.{subfolder.name}.plugin"
            self.logger.debug(
                f"[{self.name}] Trying to import subplugin: {module_name}"
            )

            try:
                module = importlib.import_module(module_name)
                plugin_factory: Optional[Callable[[], Plugin]] = getattr(
                    module, "get_plugin", None
                )

                if not callable(plugin_factory):
                    self.logger.warning(
                        f"[{self.name}] No valid get_plugin() in {module_name}"
                    )
                    continue

                subplugin = plugin_factory()
                self.logger.debug(
                    f"[{self.name}] Created subplugin instance: {subplugin.name}"
                )

                sub_config = self._config.get(subplugin.name, {})
                try:
                    subplugin.init(sub_config)
                except Exception as e:
                    self._log_plugin_error(subplugin.name, "init", e)
                    continue

                self.subplugins.append(subplugin)
                self.logger.info(f"[{self.name}] ✅ Loaded subplugin: {subplugin.name}")

                if hasattr(subplugin, "router") and isinstance(
                    subplugin.router, Router
                ):
                    self.router.include_router(subplugin.router)
                    self.logger.debug(
                        f"[{self.name}] Router included for {subplugin.name}"
                    )

            except Exception as e:
                self.logger.exception(
                    f"[{self.name}] ❌ Exception loading {module_name}: {e}"
                )

        self.logger.info(f"[{self.name}] Plugin initialization complete")

    def extend_main_menu(self, is_admin: bool = False) -> List[Dict[str, Any]]:
        """
        Extends the main menu with buttons from subplugins.

        :param is_admin: Whether the user is an admin.
        :return: List of menu buttons.
        """
        buttons: List[Dict[str, Any]] = []

        for subplugin in self.subplugins:
            if hasattr(subplugin, "extend_main_menu"):
                try:
                    buttons.extend(subplugin.extend_main_menu(is_admin))
                except Exception as e:
                    self._log_plugin_error(subplugin.name, "extend_main_menu", e)

        return buttons

    def register_aiogram(self, dp: Dispatcher) -> None:
        """
        Registers the plugin's router and subplugins' handlers and callbacks with the Dispatcher.

        :param dp: aiogram Dispatcher instance.
        """
        self.logger.info(f"[{self.name}] Registering plugin with aiogram Dispatcher")
        dp.include_router(self.router)

        for subplugin in self.subplugins:
            self._safe_call(subplugin, "register_handlers", dp)
            self._safe_call(subplugin, "register_callbacks", dp)
            self._safe_call(subplugin, "register_inline_query", dp)

        self.logger.info(f"[{self.name}] Plugin registration complete")

    def _safe_call(self, plugin: Plugin, method_name: str, *args: Any) -> None:
        if hasattr(plugin, method_name):
            try:
                getattr(plugin, method_name)(*args)
                self.logger.debug(
                    f"[{plugin.name}] {method_name} executed successfully"
                )
            except Exception as e:
                self._log_plugin_error(plugin.name, method_name, e)

    def _log_plugin_error(
        self, plugin_name: str, method: str, error: Exception
    ) -> None:
        self.logger.warning(f"[{plugin_name}] Error in {method}: {error}")


# Instantiate the plugin
plugin = MenusPlugin()
