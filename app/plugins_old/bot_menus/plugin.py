from app.plugins_old.base import Plugin
from pathlib import Path
import importlib
from typing import List, Optional, Dict, Any
from aiogram import Router, Dispatcher
from app.core.config import logger as app_logger
from logging import Logger


class MenusPlugin(Plugin):
    name = "bot_menus"
    description = "Основной плагин для меню, содержит подплагины"
    priority: int = 10

    def __init__(self, logger: Optional[Logger] = None):
        super().init()  # только если Plugin имеет __init__
        self.subplugins: List[Plugin] = []
        self.router = Router()
        self.logger = logger or app_logger
        self.name = getattr(self.__class__, "name", self.__class__.__name__)

        self.logger.info(f"[{self.name}] Plugin initialized")

    def init(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the MenusPlugin and loads subplugins.

        :param config: Configuration dictionary for the plugin and its subplugins.
        """
        self._config = config or {}
        plugins_dir = Path(__file__).parent
        self.subplugins = []
        self.logger.debug(f"[{self.name}] Scanning for subplugins in: {plugins_dir}")
        self.logger.debug(
            f"[{self.name}] Found folders: {[p.name for p in plugins_dir.iterdir() if p.is_dir()]}"
        )

        self.logger.info(f"[{self.name}] Starting plugin initialization")
        for subfolder in plugins_dir.iterdir():
            if subfolder.is_dir() and (subfolder / "plugin.py").exists():
                module_name = (
                    f"{self.__module__.rsplit('.', 1)[0]}.{subfolder.name}.plugin"
                )

                # module_name = f"app.plugins.menus.{subfolder.name}.plugin"
                self.logger.debug(f"[{self.name}] Trying to import: {module_name}")

                try:
                    module = importlib.import_module(module_name)
                    plugin_factory = getattr(module, "get_plugin", None)

                    if not plugin_factory:
                        self.logger.warning(
                            f"[{self.name}] No get_plugin() in {module_name}"
                        )
                        continue

                    subplugin = plugin_factory()
                    self.logger.debug(
                        f"[{self.name}] Created subplugin instance: {subplugin.name}"
                    )

                    sub_config = self._config.get(subplugin.name, {})
                    try:
                        subplugin.init(sub_config)
                    except Exception:
                        self.logger.exception(
                            f"[{self.name}] Failed to init subplugin: {subplugin.name}"
                        )
                        continue

                    self.subplugins.append(subplugin)
                    self.logger.info(
                        f"[{self.name}] ✅ Loaded subplugin: {subplugin.name}"
                    )

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
        buttons = []
        for subplugin in self.subplugins:
            if hasattr(subplugin, "extend_main_menu"):
                try:
                    buttons.extend(subplugin.extend_main_menu(is_admin))
                except Exception as e:
                    self.logger.warning(
                        f"[{subplugin.name}] Error in extend_main_menu: {e}"
                    )
        return buttons

    def register_aiogram(self, dp: Dispatcher) -> None:
        """
        Registers the plugin's router and subplugins' handlers and callbacks with the Dispatcher.

        :param dp: aiogram Dispatcher instance.
        """
        self.logger.info(f"[{self.name}] Registering plugin with aiogram Dispatcher")
        dp.include_router(self.router)

        for subplugin in self.subplugins:
            # Register handlers
            if hasattr(subplugin, "register_handlers"):
                try:
                    subplugin.register_handlers(dp)
                    self.logger.debug(f"[{subplugin.name}] Handlers registered")
                except Exception as e:
                    self.logger.warning(
                        f"[{subplugin.name}] Error in register_handlers: {e}"
                    )

            # Register callbacks
            if hasattr(subplugin, "register_callbacks"):
                try:
                    subplugin.register_callbacks(dp)
                    self.logger.debug(f"[{subplugin.name}] Callbacks registered")
                except Exception as e:
                    self.logger.warning(
                        f"[{subplugin.name}] Error in register_callbacks: {e}"
                    )

            # Register inline queries
            if hasattr(subplugin, "register_inline_query"):
                try:
                    subplugin.register_inline_query(dp)
                    self.logger.debug(f"[{subplugin.name}] Inline query registered")
                except Exception as e:
                    self.logger.warning(
                        f"[{subplugin.name}] Error in register_inline_query: {e}"
                    )

        self.logger.info(f"[{self.name}] Plugin registration complete")


# Instantiate the plugin
plugin = MenusPlugin()
