from asyncio import Lock
import importlib
import importlib.util
import json
import configparser
from pathlib import Path
import tomllib  # Python 3.11+
import sys
from typing import List, Optional

from app.core.config import APP_DIR, logger as app_logger
from app.core.plugin_manager.plugin_base import PluginBase, PluginContext, setup
from app.core.plugin_manager.plugin_registry import PluginRegistry

try:
    import yaml

    YAML_SUPPORTED = True
except ImportError:
    YAML_SUPPORTED = False

PLUGIN_DIR = APP_DIR / "plugins"


class PluginManager:
    _instance: Optional["PluginManager"] = None
    _lock = Lock()
    _initialized: bool = False

    def __init__(self, settings: Optional[dict] = None):
        self.settings = settings or {}
        self.logger = app_logger
        self._plugins: List[PluginBase] = []  # Инициализация списка плагинов

        self.logger.debug("PluginManager initialized")

    @classmethod
    async def ensure_initialized(cls, settings: Optional[dict] = None):
        async with cls._lock:
            if cls._initialized:
                cls._instance.logger.debug(
                    "🔁 PluginManager already initialized. Skipping."
                )
                return

            cls._instance = cls(settings)
            await cls._instance.load_plugins()
            cls._initialized = True
            cls._instance.logger.info("✅ PluginManager initialized.")

    @classmethod
    def get_instance(cls) -> "PluginManager":
        if cls._instance is None:
            raise RuntimeError(
                "PluginManager is not initialized. Call `ensure_initialized()` first."
            )
        return cls._instance

    @property
    def sorted_plugins(self):
        # Возвращаем список всех плагинов из реестра, отсортированных по приоритету
        return sorted(
            PluginRegistry.get_all(),
            key=lambda plugin: getattr(plugin.meta, "priority", 10),
        )

    @classmethod
    async def reload_all(cls, settings: Optional[dict] = None):
        async with cls._lock:
            if not cls._initialized:
                cls._instance.logger.warning(
                    "🔁 PluginManager is not initialized. Cannot reload."
                )
                return

            cls._instance.logger.info("🔄 Reloading all plugins...")
            await cls._instance.reload_plugins()
            cls._instance.logger.info("✅ Plugins reloaded.")

    async def shutdown_all_plugins(self):
        self.logger.info("🔻 Shutting down all plugins...")
        await PluginRegistry.shutdown_all()

    async def reload_all_plugins(self):
        self.logger.info("🔁 Reloading all reloadable plugins...")
        await PluginRegistry.reload_all()

    async def reload_plugins(self):
        self.logger.info("♻️ Reloading plugins...")
        self.loaded_plugins.clear()
        PluginRegistry.clear()
        await self.load_plugins()

    def load_plugin_config(self, plugin_path: Path) -> dict:
        config_data = {}
        try:
            toml_file = plugin_path / "config.toml"
            json_file = plugin_path / "config.json"
            ini_file = plugin_path / "config.ini"
            yaml_file = plugin_path / "config.yaml"

            if toml_file.exists():
                with toml_file.open("rb") as f:
                    config_data = tomllib.load(f)
            elif json_file.exists():
                with json_file.open("r", encoding="utf-8") as f:
                    config_data = json.load(f)
            elif ini_file.exists():
                parser = configparser.ConfigParser()
                parser.read(ini_file, encoding="utf-8")
                config_data = {
                    section: dict(parser.items(section))
                    for section in parser.sections()
                }
            elif yaml_file.exists() and YAML_SUPPORTED:
                with yaml_file.open("r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to load config from {plugin_path}: {e}", exc_info=True
            )
        return config_data

    async def load_plugins(self):
        self.logger.info("📦 Loading plugins from: %s", PLUGIN_DIR)
        self._plugins.clear()  # Очистка старого списка

        for plugin_path in PLUGIN_DIR.iterdir():
            await self._load_plugin_with_children(plugin_path)

    async def _load_plugin_with_children(
        self, plugin_path: Path, parent_context: Optional[PluginContext] = None
    ):
        init_file = plugin_path / "__init__.py"
        if not plugin_path.is_dir() or not init_file.exists():
            return

        rel_path = plugin_path.relative_to(APP_DIR.parent)
        module_name = ".".join(rel_path.parts)

        try:
            plugin_config = self.load_plugin_config(plugin_path)
            plugin_settings = plugin_config.get("plugin", {})

            if not plugin_settings.get("enabled", True):
                self.logger.info(f"⏭️ Skipping disabled plugin: {module_name}")
                return

            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if spec is None or spec.loader is None:
                self.logger.warning(
                    f"⚠️ Skipping plugin {module_name}: no spec or loader."
                )
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            plugin_instance = getattr(module, "plugin", None)
            if not isinstance(plugin_instance, PluginBase):
                self.logger.warning(
                    f"⚠️ {module_name} does not export a valid `plugin` instance"
                )
                return

            # **Устанавливаем путь плагина**
            plugin_instance.path = plugin_path

            plugin_context = PluginContext(settings=plugin_config)

            await plugin_instance.configure(plugin_context)
            await plugin_instance.init(plugin_context)
            await plugin_instance.integrate(plugin_context)

            PluginRegistry.register(plugin_instance)

            self.logger.info(
                f"✅ Loaded plugin: {plugin_instance.meta.name} [{module_name}]"
            )

            # Подплагины
            subplugin_names = plugin_config.get("subplugins", {}).get("enabled", [])
            for sub_name in subplugin_names:
                sub_path = plugin_path / sub_name
                await self._load_plugin_with_children(
                    sub_path, parent_context=plugin_context
                )

        except Exception as e:
            self.logger.error(
                f"❌ Failed to load plugin {module_name} from {init_file}: {e}",
                exc_info=True,
            )
