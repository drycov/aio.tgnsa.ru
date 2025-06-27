from app.plugins.base import Plugin
from app.core.config import logger
from pathlib import Path
import importlib
from typing import List
from aiogram import Router, Dispatcher


class MenusPlugin(Plugin):
    name = "menus"
    description = "Основной плагин для меню, содержит подплагины"

    def __init__(self):
        self.subplugins: List[Plugin] = []
        self.router = Router()

    def init(self, config: dict | None = None) -> None:
        self._config = config or {}
        plugins_dir = Path(__file__).parent
        self.subplugins = []

        for subfolder in plugins_dir.iterdir():
            if subfolder.is_dir() and (subfolder / "plugin.py").exists():
                module_name = f"app.plugins.menus.{subfolder.name}.plugin"
                try:
                    module = importlib.import_module(module_name)

                    plugin_factory = getattr(module, "get_plugin", None)
                    if not plugin_factory:
                        logger.warning(
                            f"[{self.name}] Подплагин {module_name} не содержит get_plugin()"
                        )
                        continue

                    subplugin = plugin_factory()
                    sub_config = self._config.get(subplugin.name, {})
                    subplugin.init(sub_config)
                    self.subplugins.append(subplugin)
                    logger.info(f"[{self.name}] Загружен подплагин: {subplugin.name}")

                    if hasattr(subplugin, "router") and isinstance(
                        subplugin.router, Router
                    ):
                        self.router.include_router(subplugin.router)

                except Exception as e:
                    logger.exception(
                        f"[{self.name}] Ошибка загрузки подплагина {module_name}"
                    )

    def extend_main_menu(self, is_admin: bool = False) -> list:
        buttons = []
        for sp in self.subplugins:
            if hasattr(sp, "extend_main_menu"):
                try:
                    buttons.extend(sp.extend_main_menu(is_admin))
                except Exception as e:
                    logger.warning(f"[{sp.name}] Ошибка при extend_main_menu: {e}")
        return buttons

    def register_aiogram(self, dp: Dispatcher) -> None:
        dp.include_router(self.router)

        for sp in self.subplugins:
            # Дополнительно регистрируем handlers
            if hasattr(sp, "register_handlers"):
                try:
                    sp.register_handlers(dp)
                    logger.debug(f"[{sp.name}] handlers зарегистрированы")
                except Exception as e:
                    logger.warning(f"[{sp.name}] Ошибка в register_handlers: {e}")

            # Дополнительно регистрируем callbacks
            if hasattr(sp, "register_callbacks"):
                try:
                    sp.register_callbacks(dp)
                    logger.debug(f"[{sp.name}] callbacks зарегистрированы")
                except Exception as e:
                    logger.warning(f"[{sp.name}] Ошибка в register_callbacks: {e}")

                    # InlineQuery
        if hasattr(sp, "register_inline_query"):
            try:
                sp.register_inline_query(dp)
                logger.debug(f"[{sp.name}] inline_query зарегистрирован")
            except Exception as e:
                logger.warning(f"[{sp.name}] Ошибка в register_inline_query: {e}")


plugin = MenusPlugin()
