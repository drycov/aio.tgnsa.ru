from typing import Dict, Optional, Type
from pathlib import Path
import asyncio

from app.core.config import APP_DIR, BASE_DIR
from app.core.logging_setup import configure_logger
from app.core.plugin_manager.interfaces import IPluginSource
from app.core.plugin_manager.base import PluginBase
from app.core.plugin_manager.sources.directory_source import PluginDirectorySource

DEFAULT_APP_DIR = APP_DIR / "plugins"
DEFAULT_CORE_DIR = APP_DIR / "core" / "plugins"
DEFAULT_EXT_DIR = BASE_DIR / "plugins"


class PluginManager:
    """
    Менеджер плагинов: полный жизненный цикл:
    загрузка → конфигурация → инициализация → регистрация.
    """

    _instance: Optional["PluginManager"] = None
    name = "PluginManager"

    def __init__(
        self,
        auto_register_sources: bool = True,
    ):
        self._sources: list[IPluginSource] = []
        self._raw_plugins: Dict[str, PluginBase] = {}
        self._active_plugins: Dict[str, PluginBase] = {}

        self._logger = configure_logger().bind(component=f"{__class__.__name__}")
        self._loaded = False
        self._configured = False
        self._initialized = False

        if auto_register_sources:
            self._logger.info("🔌 Инициализация менеджера плагинов...")

            if DEFAULT_CORE_DIR.exists():
                self._logger.debug(f"📁 System plugins: {DEFAULT_CORE_DIR}")
                self.add_source(
                    PluginDirectorySource(DEFAULT_CORE_DIR, base_class=PluginBase)
                )
            else:
                self._logger.warning(
                    f"❌ Системная директория не найдена: {DEFAULT_CORE_DIR}"
                )

            if DEFAULT_APP_DIR.exists():
                self._logger.debug(f"📁 Application plugins: {DEFAULT_APP_DIR}")
                self.add_source(
                    PluginDirectorySource(DEFAULT_APP_DIR, base_class=PluginBase)
                )
            else:
                self._logger.warning(
                    f"❌ Директория приложений не найдена: {DEFAULT_APP_DIR}"
                )

            if DEFAULT_EXT_DIR.exists():
                self._logger.debug(f"📁 External plugins: {DEFAULT_EXT_DIR}")
                self.add_source(
                    PluginDirectorySource(DEFAULT_EXT_DIR, base_class=PluginBase)
                )
            else:
                self._logger.warning(
                    f"❌ Внешняя директория не найдена: {DEFAULT_EXT_DIR}"
                )

    # ---------------- Singleton Access ----------------

    @classmethod
    def get_instance(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def create_once(cls) -> "PluginManager":
        return cls.get_instance()

    # ---------------- Source Management ----------------

    def add_source(self, source: IPluginSource) -> None:
        self._sources.append(source)
        self._logger.debug(f"🔌 Источник добавлен: {type(source).__name__}")

    # ---------------- Plugin Lifecycle ----------------

    def load_plugins(self) -> None:
        if self._loaded:
            return

        self._raw_plugins.clear()
        for source in self._sources:
            plugins = source.load_plugins() or {}
            for name, plugin in plugins.items():
                if not isinstance(plugin, PluginBase):
                    self._logger.warning(
                        f"⛔ Плагин '{name}' не наследует PluginBase — пропущен."
                    )
                    continue
                self._raw_plugins[name] = plugin
                self._logger.debug(f"📥 Загружен плагин: {name}")

        self._loaded = True
        self._logger.info(f"📦 Загружено {len(self._raw_plugins)} плагинов")

    async def load_plugins_async(self) -> None:
        """Асинхронная версия загрузки плагинов."""
        if self._loaded:
            return
        self._raw_plugins.clear()
        for source in self._sources:
            if hasattr(source, "load_async") and callable(
                getattr(source, "load_async")
            ):
                plugins = await source.load_async()
            else:
                plugins = source.load()
            for name, plugin in plugins.items():
                if not isinstance(plugin, PluginBase):
                    self._logger.warning(
                        f"⛔ Плагин '{name}' не наследует PluginBase — пропущен."
                    )
                    continue
                self._raw_plugins[name] = plugin
                self._logger.debug(f"📥 Загружен плагин: {name}")
        self._loaded = True
        self._logger.info(f"📦 Загружено {len(self._raw_plugins)} плагинов (async)")

    def configure_plugins(self) -> None:
        if self._configured:
            return
        for name, plugin in self._raw_plugins.items():
            if hasattr(plugin, "load_config"):
                try:
                    plugin_dir = getattr(plugin, "__plugin_dir__", None)
                    if plugin_dir is not None:
                        plugin.load_config(plugin_dir)
                    else:
                        plugin.load_config()
                    self._logger.debug(f"⚙️ Конфигурация загружена: {name}")
                except Exception as e:
                    self._logger.error(f"❌ Конфигурация '{name}': {e}")
        self._configured = True

    def initialize_plugins(self, settings: Optional[dict] = None) -> None:
        if self._initialized:
            return
        for name, plugin in self._raw_plugins.items():
            try:
                plugin.init(settings or {})
                self._active_plugins[name] = plugin
                meta = getattr(plugin, "meta", None)
                if meta:
                    self._logger.info(
                        f"🟢 Инициализирован: {meta.name} v{meta.version}"
                    )
                else:
                    self._logger.info(f"🟢 Инициализирован: {name}")
            except Exception as e:
                self._logger.error(f"❌ Инициализация '{name}': {e}")
        self._initialized = True

    # ---------------- Composite Init ----------------

    def full_load_cycle(self, settings: Optional[dict] = None) -> None:
        """Полный жизненный цикл плагинов."""
        self.ensure_ready(settings)

    def ensure_ready(self, settings: Optional[dict] = None) -> None:
        self.ensure_loaded()
        self.ensure_configured()
        self.ensure_initialized(settings)

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_plugins()

    def ensure_configured(self) -> None:
        if not self._configured:
            self.configure_plugins()

    def ensure_initialized(self, settings: Optional[dict] = None) -> None:
        if not self._initialized:
            self.initialize_plugins(settings)

    # ---------------- Accessors ----------------

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        return self._active_plugins.get(name)

    def all_plugins(self) -> Dict[str, PluginBase]:
        return self._active_plugins

    def all_meta(self) -> list:
        return [p.meta for p in self._active_plugins.values() if hasattr(p, "meta")]

    @property
    def sorted_plugins(self) -> list[PluginBase]:
        """
        Возвращает список активных плагинов, отсортированных по приоритету (если есть meta.priority), иначе по имени.
        """
        plugins = list(self._active_plugins.values())

        def get_priority(plugin):
            meta = getattr(plugin, "meta", None)
            if meta and hasattr(meta, "priority"):
                return meta.priority
            return 100  # default low priority

        return sorted(
            plugins,
            key=lambda p: (get_priority(p), getattr(p.meta, "name", str(p))),
        )

    # ---------------- Status ----------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def is_configured(self) -> bool:
        return self._configured

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    ""
