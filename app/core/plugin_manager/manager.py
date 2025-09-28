from __future__ import annotations
from typing import Optional
from pathlib import Path
import traceback
import inspect
from dataclasses import dataclass

from app.core.config import APP_DIR, BASE_DIR
from app.core.logging_setup import configure_logger
from app.core.plugin_manager.interfaces import IPluginSource
from app.core.plugin_manager.base import PluginBase
from app.core.plugin_manager.sources.directory_source import PluginDirectorySource

DEFAULT_APP_DIR = APP_DIR / "plugins"
DEFAULT_CORE_DIR = APP_DIR / "core" / "plugins"
DEFAULT_EXT_DIR = BASE_DIR / "plugins"


@dataclass
class PluginManagerStatus:
    """Сводка состояния менеджера плагинов."""
    sources: int = 0
    loaded: int = 0
    active: int = 0
    is_loaded: bool = False
    is_configured: bool = False
    is_initialized: bool = False

    def as_dict(self) -> dict:
        return self.__dict__.copy()

    def __str__(self) -> str:
        return (
            f"PluginManagerStatus(sources={self.sources}, "
            f"loaded={self.loaded}, active={self.active}, "
            f"loaded?={self.is_loaded}, "
            f"configured?={self.is_configured}, "
            f"initialized?={self.is_initialized})"
        )


class PluginManager:
    """
    Менеджер плагинов: полный жизненный цикл:
    загрузка → конфигурация → инициализация → регистрация.
    """

    _instance: Optional["PluginManager"] = None
    name = "PluginManager"

    def __init__(self, auto_register_sources: bool = True) -> None:
        self._sources: list[IPluginSource] = []
        self._raw_plugins: dict[str, PluginBase] = {}
        self._active_plugins: dict[str, PluginBase] = {}

        self._logger = configure_logger().bind(component=self.__class__.__name__)
        self._loaded = False
        self._configured = False
        self._initialized = False

        if auto_register_sources:
            self._register_default_sources()

    # ---------------- Singleton Access ----------------

    @classmethod
    def get_instance(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def create_once(cls) -> "PluginManager":
        return cls.get_instance()

    # ---------------- Sources ----------------

    def _register_default_sources(self) -> None:
        self._logger.info("🔌 Инициализация менеджера плагинов...")

        for label, path in [
            ("System", DEFAULT_CORE_DIR),
            ("Application", DEFAULT_APP_DIR),
            ("External", DEFAULT_EXT_DIR),
        ]:
            if path.exists():
                self._logger.debug(f"📁 {label} plugins: {path}")
                self.add_source(PluginDirectorySource(path, base_class=PluginBase))
            else:
                self._logger.warning(f"❌ {label} директория не найдена: {path}")

    def add_source(self, source: IPluginSource) -> None:
        self._sources.append(source)
        self._logger.debug(f"🔌 Источник добавлен: {type(source).__name__}")

    # ---------------- Core Lifecycle ----------------

    def _require_ready(self) -> None:
        """Гарантирует, что плагины инициализированы перед доступом."""
        if not self._initialized:
            raise RuntimeError(
                "⚠️ PluginManager is not initialized. "
                "Вызови ensure_ready() перед использованием плагинов."
            )

    def load_plugins(self) -> dict[str, PluginBase]:
        if self._loaded:
            return self._raw_plugins

        self._raw_plugins.clear()
        for source in self._sources:
            try:
                plugins = source.load_plugins() if hasattr(source, "load_plugins") else {}
                for name, plugin in (plugins or {}).items():
                    if not isinstance(plugin, PluginBase):
                        self._logger.warning(
                            f"⛔ Плагин '{name}' не наследует PluginBase — пропущен."
                        )
                        continue
                    self._raw_plugins[name] = plugin
                    self._logger.debug(f"📥 Загружен плагин: {name}")
            except Exception as e:
                self._logger.error(
                    f"❌ Ошибка при загрузке из {type(source).__name__}: {e}\n{traceback.format_exc()}"
                )

        self._loaded = True
        self._logger.info(f"📦 Загружено {len(self._raw_plugins)} плагинов")
        return self._raw_plugins

    async def load_plugins_async(self) -> dict[str, PluginBase]:
        if self._loaded:
            return self._raw_plugins

        self._raw_plugins.clear()
        for source in self._sources:
            try:
                if hasattr(source, "load_async") and inspect.iscoroutinefunction(source.load_async):
                    plugins = await source.load_async()
                else:
                    plugins = source.load_plugins()
                for name, plugin in (plugins or {}).items():
                    if not isinstance(plugin, PluginBase):
                        self._logger.warning(
                            f"⛔ Плагин '{name}' не наследует PluginBase — пропущен."
                        )
                        continue
                    self._raw_plugins[name] = plugin
                    self._logger.debug(f"📥 Загружен плагин: {name}")
            except Exception as e:
                self._logger.error(
                    f"❌ Ошибка при async-загрузке из {type(source).__name__}: {e}\n{traceback.format_exc()}"
                )

        self._loaded = True
        self._logger.info(f"📦 Загружено {len(self._raw_plugins)} плагинов (async)")
        return self._raw_plugins

    def configure_plugins(self) -> None:
        if self._configured:
            return
        for name, plugin in self._raw_plugins.items():
            if hasattr(plugin, "load_config"):
                try:
                    plugin.load_config(getattr(plugin, "__plugin_dir__", None))
                    self._logger.debug(f"⚙️ Конфигурация загружена: {name}")
                except Exception as e:
                    self._logger.error(
                        f"❌ Конфигурация '{name}': {e}\n{traceback.format_exc()}"
                    )
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
                    self._logger.info(f"🟢 Инициализирован: {meta.name} v{meta.version}")
                else:
                    self._logger.info(f"🟢 Инициализирован: {name}")
            except Exception as e:
                self._logger.error(
                    f"❌ Инициализация '{name}': {e}\n{traceback.format_exc()}"
                )
        self._initialized = True

    # ---------------- Composite Init ----------------

    def full_load_cycle(self, settings: Optional[dict] = None) -> None:
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

    def reload(self) -> None:
        self._loaded = self._configured = self._initialized = False
        self._raw_plugins.clear()
        self._active_plugins.clear()
        self._logger.info("🔄 Перезагрузка плагинов...")
        self.full_load_cycle()

    def shutdown(self) -> None:
        for name, plugin in self._active_plugins.items():
            if hasattr(plugin, "shutdown"):
                try:
                    plugin.shutdown()
                    self._logger.info(f"🛑 Завершён: {name}")
                except Exception as e:
                    self._logger.error(
                        f"❌ Ошибка при shutdown '{name}': {e}\n{traceback.format_exc()}"
                    )

    # ---------------- Accessors ----------------

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        self._require_ready()
        return self._active_plugins.get(name)

    def all_plugins(self) -> dict[str, PluginBase]:
        self._require_ready()
        return self._active_plugins

    def all_meta(self) -> list:
        self._require_ready()
        return [p.meta for p in self._active_plugins.values() if hasattr(p, "meta")]

    @property
    def sorted_plugins(self) -> list[PluginBase]:
        self._require_ready()

        def get_priority(plugin: PluginBase) -> int:
            meta = getattr(plugin, "meta", None)
            return getattr(meta, "priority", 100)

        return sorted(
            self._active_plugins.values(),
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

    def summary(self) -> PluginManagerStatus:
        status = PluginManagerStatus(
            sources=len(self._sources),
            loaded=len(self._raw_plugins),
            active=len(self._active_plugins),
            is_loaded=self._loaded,
            is_configured=self._configured,
            is_initialized=self._initialized,
        )
        if not status.is_initialized:
            self._logger.warning("⚠️ summary(): плагины ещё не инициализированы. Используй ensure_ready()")
        return status

    # ---------------- Representation ----------------

    def __repr__(self) -> str:
        return f"<PluginManager {self.summary()}>"
