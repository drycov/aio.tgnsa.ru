import os
import tempfile
import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type
from collections import defaultdict
from functools import lru_cache

import tomli_w
import tomllib
from fastapi import APIRouter, FastAPI

from app.core.config import BASE_DIR, PLUGIN_CONGIG_DIR, APP_DIR
from app.plugins.base import Plugin

logger = logging.getLogger("PluginManager")


class PluginManager:
    _instance: Optional["PluginManager"] = None
    _initialized = False

    def __init__(self, plugin_dir: Optional[Path] = None, plugin_config_file: Optional[Path] = None):
        if PluginManager._instance is not None:
            raise RuntimeError("PluginManager is a singleton. Use PluginManager.get_instance()")

        self.plugin_dir = plugin_dir or APP_DIR / "plugins"
        self.plugin_config_file = plugin_config_file or (PLUGIN_CONGIG_DIR / "plugins.toml")
        
        # Plugin storage
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_configs: Dict[str, dict] = {}
        self.core_plugins: Dict[str, Plugin] = {}
        self.sorted_plugins: List[Plugin] = []
        
        # Core plugins that should always be loaded
        self.core_plugin_modules = [
            "app.plugins.plugins_ui",
            "app.plugins.healthcheck",
            "app.plugins.config_viewer"
        ]
        
        # Cache for performance
        self._config_cache: Dict[str, dict] = {}
        self._module_cache: Dict[str, Any] = {}
        
        PluginManager._instance = self

    # --- Core Methods ---
    
    def post_init_integration(self) -> None:
        """Связывает плагины после инициализации, например, регистрацию в healthcheck."""
        health_plugin = self.plugins.get("healthcheck")
        if not health_plugin or not getattr(health_plugin, "enabled", False):
            logger.warning("⚠️ Healthcheck plugin не найден или отключён")
            return

        for plugin in self.plugins.values():
            if not getattr(plugin, "enabled", False):
                continue

            if hasattr(plugin, "register_healthcheck"):
                try:
                    plugin.register_healthcheck(health_plugin)
                    logger.debug(f"🔗 {plugin.name} зарегистрировал проверки в healthcheck")
                except Exception as e:
                    logger.warning(f"⚠️ {plugin.name} не смог зарегистрировать healthcheck: {e}")

        
    def load_all(self) -> None:
        """Load all plugins from all sources and resolve dependencies."""
        if self._initialized:
            logger.warning("⚠️ PluginManager already initialized")
            return
            
        logger.info(f"🔍 Scanning plugin directory: {self.plugin_dir}")
        
        self._load_plugin_config_file()
        self._load_core_plugins()
        self._load_local_plugins()
        self._load_entrypoint_plugins()
        self._resolve_dependencies()
        
        logger.info(f"✅ Loaded {len(self.sorted_plugins)} plugins")
        self._initialized = True

    def init_all(self, settings: Any) -> None:
        """Initialize all loaded plugins with their configurations."""
        if not self._initialized:
            raise RuntimeError("PluginManager not initialized. Call load_all() first")
            
        for plugin in self.sorted_plugins:
            self._init_plugin(plugin, settings)

    # --- Plugin Loading ---

    def _load_core_plugins(self) -> None:
        """Load core plugins that are bundled with the application."""
        for module_path in self.core_plugin_modules:
            try:
                self._load_plugin_from_module(module_path, source_prefix="core")
            except Exception as e:
                logger.exception(f"❌ Failed to load core plugin '{module_path}': {e}")

    def _load_local_plugins(self) -> None:
        """Load plugins from the local plugins directory."""
        for path in self.plugin_dir.glob("*/__init__.py"):
            plugin_module = path.parent.name
            module_path = f"app.plugins.{plugin_module}"
            
            if plugin_module in self.core_plugins:
                logger.debug(f"🔁 Skipping local plugin '{plugin_module}' (core plugin exists)")
                continue
                
            try:
                self._load_plugin_from_module(module_path, source_prefix="local")
            except Exception as e:
                logger.exception(f"❌ Failed to load plugin '{plugin_module}': {e}")

    def _load_entrypoint_plugins(self) -> None:
        """Load plugins registered via package entry points."""
        try:
            entry_points = importlib.metadata.entry_points()
            plugin_eps = entry_points.select(group="tgnms.plugins")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load entry points: {e}")
            return

        for ep in plugin_eps:
            if ep.name in self.core_plugins:
                logger.debug(f"🔁 Skipping entrypoint plugin '{ep.name}' (core plugin exists)")
                continue
                
            try:
                self._load_plugin_from_entrypoint(ep)
            except Exception as e:
                logger.warning(f"❌ Failed to load plugin from entrypoint '{ep.name}': {e}")

    def _load_plugin_from_module(self, module_path: str, source_prefix: str) -> None:
        """Load a single plugin from a Python module."""
        if module_path in self._module_cache:
            return
            
        spec = importlib.util.find_spec(module_path)
        if not spec:
            logger.warning(f"⛔ No spec found for: {module_path}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_path] = module
        spec.loader.exec_module(module)
        self._module_cache[module_path] = module

        plugin: Plugin = getattr(module, "plugin", None)
        if not isinstance(plugin, Plugin):
            logger.warning(f"⚠️ Skipped non-Plugin: {module_path}")
            return

        self._configure_plugin(plugin, module)
        self._add_plugin(plugin, source=f"{source_prefix}:{module_path}")
        
        if source_prefix == "core":
            self.core_plugins[plugin.name] = plugin

    def _load_plugin_from_entrypoint(self, ep) -> None:
        """Load a plugin from an entry point."""
        plugin: Plugin = ep.load()
        if not isinstance(plugin, Plugin):
            logger.warning(f"⚠️ Skipped non-Plugin from entrypoint: {ep.name}")
            return

        self._configure_plugin(plugin)
        self._add_plugin(plugin, source=f"entrypoint:{ep.name}")

    def _configure_plugin(self, plugin: Plugin, module=None) -> None:
        """Set default plugin attributes."""
        plugin.name = getattr(plugin, "name", 
                            getattr(plugin, "__module__", "").split(".")[-1])
        plugin.priority = getattr(plugin, "priority", 100)
        plugin.depends_on = getattr(plugin, "depends_on", [])
        plugin.description = getattr(plugin, "description", "")
        
        if module:
            plugin.config_class = getattr(module, "PluginConfig", None)

    # --- Configuration Management ---

    def _load_plugin_config_file(self) -> None:
        """Load the global plugin configuration file."""
        if not self.plugin_config_file.exists():
            logger.warning(f"⚠️ Plugin config file not found: {self.plugin_config_file}")
            return
            
        try:
            with self.plugin_config_file.open("rb") as f:
                self.plugin_configs = tomllib.load(f)
            logger.info(f"📦 Loaded plugin configs from: {self.plugin_config_file}")
        except Exception as e:
            content = self.plugin_config_file.read_text(encoding="utf-8", errors="ignore")[:500]
            logger.error(f"❌ Failed to load plugin config: {e}\nFile preview:\n{content}")

    def atomic_write(self, path: Path, data: dict) -> None:
        """Atomically write a TOML file."""
        try:
            with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as tmp:
                tomli_w.dump(data, tmp)
                tmp_path = Path(tmp.name)
            
            os.replace(tmp_path, path)
            logger.debug(f"📝 Atomic write succeeded for {path}")
        except Exception as e:
            logger.error(f"❌ Atomic write failed for {path}: {e}")
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def generate_global_plugin_config(self) -> None:
        """Generate global config from all local plugin configs."""
        aggregated = {}
        
        for path in self.plugin_dir.glob("*/config.toml"):
            plugin_name = path.parent.name
            try:
                with path.open("rb") as f:
                    aggregated[plugin_name] = tomllib.load(f)
                logger.debug(f"📄 Added config for '{plugin_name}' from {path}")
            except Exception as e:
                logger.error(f"❌ Failed to load config for '{plugin_name}': {e}")

        self.plugin_config_file.parent.mkdir(parents=True, exist_ok=True)
        self.atomic_write(self.plugin_config_file, aggregated)
        logger.info(f"✅ Generated global config at {self.plugin_config_file}")

    # --- Plugin Initialization ---

    def _init_plugin(self, plugin: Plugin, settings: Any) -> None:
        """Initialize a single plugin with merged configuration."""
        try:
            config = self._get_plugin_config(plugin, settings)
            
            enabled = config.get("enabled", True)
            setattr(plugin, "enabled", enabled)
            
            if not enabled:
                logger.info(f"⏸️ Plugin '{plugin.name}' disabled via config")
                return

            plugin.init(config)
            logger.info(f"🛠️ Initialized plugin: {plugin.name}")
            
        except Exception as e:
            logger.error(f"⚠️ Plugin '{plugin.name}' init failed: {e}")
            setattr(plugin, "enabled", False)

    def _get_plugin_config(self, plugin: Plugin, settings: Any) -> dict:
        """Get merged configuration for a plugin."""
        plugin_path = Path(sys.modules[plugin.__module__].__file__).parent

        # Base configuration
        config = {
            "path": f"/{plugin.name.replace('_', '-')}",
            "plugin_dir": plugin_path,
            "static_url": getattr(settings.app, "static_url", "/static"),
            "favicon_url": getattr(settings.app, "favicon_url", "/favicon.ico"),
            "templates_dir": plugin_path / "templates",
            "config_file": plugin_path / "config.toml",
            "log_dir": BASE_DIR / "logs" / plugin.name,
            "data_dir": BASE_DIR / "data" / plugin.name,
            "priority": getattr(plugin, "priority", 100),
            "depends_on": getattr(plugin, "depends_on", []),
        }
        
        # Local config
        local_config = {}
        if config["config_file"].exists():
            try:
                with config["config_file"].open("rb") as f:
                    local_config = tomllib.load(f)
            except Exception as e:
                logger.error(f"❌ Failed to load local config for {plugin.name}: {e}")
        
        # Global config
        global_config = self.plugin_configs.get(plugin.name, {})
        
        # Settings config
        settings_config = {}
        settings_attr = getattr(settings, plugin.name, None)
        if settings_attr:
            if hasattr(settings_attr, "model_dump"):
                settings_config = settings_attr.model_dump()
            elif isinstance(settings_attr, dict):
                settings_config = settings_attr
            elif hasattr(settings_attr, "__dict__"):
                settings_config = vars(settings_attr)
        
        return {**config, **local_config, **global_config, **settings_config}

    # --- Dependency Resolution ---

    def _resolve_dependencies(self) -> None:
        """Resolve plugin dependencies using topological sort."""
        visited: Set[str] = set()
        stack: Set[str] = set()
        result: List[str] = []

        def visit(name: str) -> None:
            if name in stack:
                raise RuntimeError(f"❌ Cyclic dependency: {' -> '.join(stack)} -> {name}")
            if name in visited:
                return
                
            stack.add(name)
            plugin = self.plugins.get(name)
            if not plugin:
                raise RuntimeError(f"❌ Plugin '{name}' not found")
                
            for dep in plugin.depends_on:
                visit(dep)
                
            stack.remove(name)
            visited.add(name)
            result.append(name)

        # Sort by priority (highest first)
        for name in sorted(self.plugins, key=lambda n: -self.plugins[n].priority):
            visit(name)

        self.sorted_plugins = [self.plugins[name] for name in result]

    # --- Plugin Management ---

    def _add_plugin(self, plugin: Plugin, source: str) -> None:
        """Add a plugin to the manager."""
        if plugin.name in self.plugins:
            logger.warning(f"⚠️ Duplicate plugin '{plugin.name}' from {source}")
            return
            
        self.plugins[plugin.name] = plugin
        logger.info(f"✅ Registered plugin: {plugin.name} ({source})")

    def reload_plugin(self, plugin_name: str, app: Any = None, dp: Any = None, scheduler: Any = None) -> bool:
        """Reload a plugin and its routes/handlers."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"🔁 Cannot reload unknown plugin '{plugin_name}'")
            return False

        try:
            # Remove existing routes/handlers
            self._unregister_plugin(plugin_name, app, dp, scheduler)
            
            # Reload the module
            if not self._reload_plugin_module(plugin):
                return False
                
            # Reinitialize
            plugin_config = self.plugin_configs.get(plugin_name, {})
            if plugin.config_class:
                config = plugin.config_class(**plugin_config)
                plugin.init(config)
            else:
                plugin.init(None)
                
            # Reregister
            self._register_plugin(plugin, app, dp, scheduler)
            
            logger.info(f"🔁 Successfully reloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.exception(f"❌ Failed to reload plugin '{plugin_name}': {e}")
            return False

    def _reload_plugin_module(self, plugin: Plugin) -> bool:
        """Reload a plugin's Python module."""
        module_path = plugin.__module__

        try:
            return self._extracted_from__reload_plugin_module_6(module_path, plugin)
        except Exception as e:
            logger.exception(f"❌ Failed to reload module '{module_path}': {e}")
            return False

    # TODO Rename this here and in `_reload_plugin_module`
    def _extracted_from__reload_plugin_module_6(self, module_path, plugin):
        if module_path in sys.modules:
            del sys.modules[module_path]
            if module_path in self._module_cache:
                del self._module_cache[module_path]

        module = importlib.import_module(module_path)
        importlib.reload(module)
        self._module_cache[module_path] = module

        new_plugin = getattr(module, "plugin", None)
        if not isinstance(new_plugin, Plugin):
            logger.error("⚠️ Reloaded module doesn't contain valid Plugin")
            return False

        plugin.__dict__.update(new_plugin.__dict__)
        return True

    # --- Framework Integration ---

    def register_fastapi(self, app: FastAPI) -> None:
        """Register all plugins with FastAPI."""
        for plugin in self.sorted_plugins:
            if not getattr(plugin, "enabled", True):
                continue
                
            try:
                if hasattr(plugin, "router") and isinstance(plugin.router, APIRouter):
                    self._register_fastapi_router(app, plugin)
                elif hasattr(plugin, "register_fastapi"):
                    plugin.register_fastapi(app)
                    
                logger.debug(f"🌐 Registered FastAPI routes: {plugin.name}")
            except Exception as e:
                logger.warning(f"⚠️ FastAPI registration failed for {plugin.name}: {e}")

    def _register_fastapi_router(self, app: FastAPI, plugin: Plugin) -> None:
        """Register a plugin's APIRouter with FastAPI."""
        # Ensure all routes are tagged with the plugin name
        for route in plugin.router.routes:
            if not hasattr(route, "tags"):
                route.tags = []
            if plugin.name not in route.tags:
                route.tags.append(plugin.name)
                
        app.include_router(plugin.router)

    def _unregister_plugin(self, plugin_name: str, app: Any, dp: Any, scheduler: Any) -> None:
        """Unregister a plugin from all frameworks."""
        if app:
            removed = self._remove_fastapi_routes(app, plugin_name)
            logger.debug(f"🧹 Removed {removed} FastAPI routes for {plugin_name}")
            
        if dp and hasattr(dp, "unregister_plugin_handlers"):
            dp.unregister_plugin_handlers(plugin_name)
            
        if scheduler and hasattr(scheduler, "unregister_plugin_jobs"):
            scheduler.unregister_plugin_jobs(plugin_name)

    def _register_plugin(self, plugin: Plugin, app: Any, dp: Any, scheduler: Any) -> None:
        """Register a plugin with all frameworks."""
        if app and hasattr(plugin, "register_fastapi"):
            plugin.register_fastapi(app)
            
        if dp and hasattr(plugin, "register_aiogram"):
            plugin.register_aiogram(dp)
            
        if scheduler and hasattr(plugin, "register_scheduler"):
            plugin.register_scheduler(scheduler)

    def _remove_fastapi_routes(self, app: FastAPI, plugin_name: str) -> int:
        """Remove all routes for a plugin from FastAPI."""
        original_count = len(app.router.routes)
        app.router.routes = [
            route for route in app.router.routes
            if plugin_name not in getattr(route, "tags", [])
        ]
        return original_count - len(app.router.routes)

    # --- Singleton Access ---

    @staticmethod
    def get_instance() -> Optional["PluginManager"]:
        """Get the singleton instance."""
        return PluginManager._instance

    @staticmethod
    def create_once(plugin_dir: Optional[Path] = None, 
                   plugin_config_file: Optional[Path] = None) -> "PluginManager":
        """Create or get the singleton instance."""
        if PluginManager._instance is None:
            PluginManager._instance = PluginManager(plugin_dir, plugin_config_file)
        return PluginManager._instance