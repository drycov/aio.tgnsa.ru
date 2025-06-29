from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
from typing import TYPE_CHECKING, Any, Optional, Union
from app.core.config import logger

if TYPE_CHECKING:
    from fastapi import FastAPI, APIRouter
    from aiogram import Dispatcher
    from apscheduler.schedulers.asyncio import AsyncIOScheduler


# 🔧 Plugin Metadata
@dataclass
class PluginMetadata:
    """
    Metadata for a plugin, including its name, version, description, priority, enabled status, and dependencies.

    Attributes:
        name (str): The name of the plugin.
        version (str): The version of the plugin.
        description (str): A brief description of the plugin.
        priority (int): The priority of the plugin (lower values indicate higher priority).
        enabled (bool): Whether the plugin is enabled.
        dependencies (list[str]): A list of dependencies required by the plugin.
    """

    name: str
    version: Optional[str] = None
    author: Optional[str] = None  # Добавляем автора

    description: str = ""
    priority: int = 10
    enabled: bool = True
    dependencies: list[str] = field(default_factory=list)

    # def resolve_version(self, plugin_path: Path, config: Optional[dict] = None) -> str:
    #     """Resolve version from config > VERSION file > git (if available)."""
    #     # 1. Из конфига
    #     if config:
    #         version = config.get("plugin", {}).get("version")
    #         if version:
    #             return version

    #     # 2. Из VERSION файла
    #     version_file = plugin_path / "VERSION"
    #     if version_file.exists():
    #         try:
    #             return version_file.read_text(encoding="utf-8").strip()
    #         except Exception:
    #             pass

    #     # 3. Из git describe (если доступен)
    #     try:
    #         import subprocess
    #         result = subprocess.run(
    #             ["git", "describe", "--tags", "--always"],
    #             cwd=plugin_path,
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.DEVNULL,
    #             text=True,
    #             timeout=1
    #         )
    #         if result.returncode == 0:
    #             return result.stdout.strip()
    #     except Exception:
    #         pass

    #     return "0.0.0"


# 🧩 Plugin Execution Context
@dataclass
class PluginContext:
    """
    Context for plugin execution, including references to FastAPI app, Aiogram dispatcher, scheduler, settings, and shared data.

    Attributes:
        app (FastAPI): The FastAPI application instance.
        dp (Dispatcher): The Aiogram dispatcher instance.
        scheduler (AsyncIOScheduler): The APScheduler instance.
        settings (dict): Plugin-specific settings.
        shared (dict): Shared data between plugins.
    """

    app: Optional["FastAPI"] = None
    dp: Optional["Dispatcher"] = None
    scheduler: Optional["AsyncIOScheduler"] = None
    settings: Optional[dict] = None
    shared: dict[str, Any] = field(default_factory=dict)


class Stoppable(ABC):
    """
    Interface for objects that can be stopped asynchronously.

    Methods:
        shutdown(): Asynchronous hook for shutting down the object.
    """

    @abstractmethod
    async def shutdown(self) -> None:
        """Asynchronous hook for shutting down the object."""
        ...


class Reloadable(ABC):
    """
    Interface for objects that can be reloaded asynchronously.

    Methods:
        reload(): Asynchronous hook for reloading the object.
    """

    @abstractmethod
    async def reload(self) -> None:
        """Asynchronous hook for reloading the object."""
        ...


class Startable(ABC):
    """
    Interface for objects that can be started asynchronously.

    Methods:
        startup(): Asynchronous hook for starting the object.
    """

    @abstractmethod
    async def startup(self) -> None:
        """Asynchronous hook for starting the object."""
        ...


# 🔌 Abstract Base Class for Plugins
class PluginBase(ABC):
    """
    Abstract base class for plugins, providing a common interface and basic functionality.

    Attributes:
        meta (PluginMetadata): Metadata for the plugin.
        router (APIRouter): FastAPI router for the plugin.
        dp (Dispatcher): Aiogram dispatcher for the plugin.
        scheduler (AsyncIOScheduler): APScheduler instance for the plugin.
        logger (Logger): Logger instance for the plugin.
        status (dict): Status information for the plugin.
        context (PluginContext): Execution context for the plugin.
    """

    meta: PluginMetadata = PluginMetadata(name="unnamed_plugin")
    path: Optional[Path] = None  # Добавьте поле для пути к плагину

    router: Optional["APIRouter"] = None
    dp: Optional["Dispatcher"] = None
    scheduler: Optional["AsyncIOScheduler"] = None

    def __init__(self):
        """
        Initialize a new instance of PluginBase.

        Initializes the logger and logs the creation of the plugin instance.
        """
        self.logger = logger
        self.status: dict[str, Any] = {}
        self.context: Optional[PluginContext] = None
        self.logger.debug(f"⚙️ Plugin instance created: {self.meta.name}")

    @abstractmethod
    async def configure(self, settings: Optional[dict] = None) -> None:
        self._resolve_version(settings)

    def _resolve_version(self, settings: Optional[dict]) -> None:
        """Automatically resolves the plugin version."""
        if self.meta.version:
            return  # Already set manually

        version = None

        # 1. Из config
        version = settings.get("plugin", {}).get("version") if settings else None
        if version:
            self.logger.debug(f"📦 Version from config: {version}")
            self.meta.version = version
            return

        # 2. Из VERSION файла
        if self.path:
            version_file = self.path / "VERSION"
            if version_file.exists():
                try:
                    version = version_file.read_text(encoding="utf-8").strip()
                    self.logger.debug(f"📄 Version from VERSION file: {version}")
                    self.meta.version = version
                    return
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to read VERSION file: {e}")

            # 3. Из git describe
            try:
                result = subprocess.run(
                    ["git", "describe", "--tags", "--always"],
                    cwd=self.path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.logger.debug(f"🔧 Version from git: {version}")
                    self.meta.version = version
                    return
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to get git version: {e}")

        # fallback
        self.meta.version = "0.0.0"
        self.logger.debug("🛑 No version found. Using fallback: 0.0.0")

    # 🚀 Main initialization of the plugin (resources, services)
    @abstractmethod
    async def init(self, settings: Optional[dict] = None) -> None:
        """
        Asynchronous hook for initializing the plugin.

        Args:
            settings (dict): Plugin-specific settings.
        """
        ...

    # 🔌 Integration with external systems
    @abstractmethod
    def integrate(self, context: PluginContext) -> None:
        """
        Synchronous hook for integrating the plugin with external systems.

        Args:
            context (PluginContext): Execution context for the plugin.
        """
        ...

    # 📡 Health check for the plugin
    def healthcheck(self) -> Union[str, dict]:
        """
        Returns the health status of the plugin.

        Returns:
            str or dict: Health status of the plugin.
        """
        return self.status if self.status else "ok"

    # 🛠️ Registration in FastAPI
    def register_fastapi(self, app: "FastAPI") -> None:
        """
        Registers the plugin's routes with the FastAPI application.

        Args:
            app (FastAPI): The FastAPI application instance.
        """
        if self.router:
            app.include_router(self.router)
            self.logger.debug(f"🔌 FastAPI routes registered: {self.meta.name}")

    # 🛠️ Registration in Aiogram
    def register_aiogram(self, dp: "Dispatcher") -> None:
        """
        Registers the plugin's handlers with the Aiogram dispatcher.

        Args:
            dp (Dispatcher): The Aiogram dispatcher instance.
        """
        if self.dp:
            dp.include_router(self.dp)
            self.logger.debug(f"🤖 Aiogram handlers registered: {self.meta.name}")

    # 🛠️ Registration in APScheduler
    def register_scheduler(self, scheduler: "AsyncIOScheduler") -> None:
        """
        Integrates the plugin with the APScheduler instance.

        Args:
            scheduler (AsyncIOScheduler): The APScheduler instance.
        """
        if self.scheduler:
            self.logger.debug(f"⏰ Scheduler integration complete: {self.meta.name}")

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def version(self) -> Optional[str]:
        return self.meta.version

    @property
    def description(self) -> str:
        return self.meta.description

    @property
    def author(self) -> Optional[str]:
        return getattr(self.meta, "author", None)

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} version={self.version}>"


async def setup(plugin: PluginBase, context: PluginContext) -> None:
    """
    Sets up the plugin by configuring, initializing, and integrating it with the provided context.

    Args:
        plugin (PluginBase): The plugin instance to set up.
        context (PluginContext): The execution context for the plugin.

    Raises:
        Exception: If any part of the setup process fails.
    """
    plugin.logger.debug(f"🧪 Setup started: {plugin.meta.name}")

    plugin.context = context  # Save the context for use within the plugin
    try:
        await plugin.configure(context.settings)
        await plugin.init(context.settings)
        plugin.integrate(context)
        plugin.logger.info(f"✅ Plugin setup complete: {plugin.meta.name}")
    except Exception as ex:
        plugin.logger.exception(f"❌ Plugin setup failed: {plugin.meta.name} — {ex}")
        raise
