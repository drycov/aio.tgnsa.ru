from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from app.core.plugin_manager.descriptors import PluginMeta


class PluginBase(ABC):
    """Base class for all plugins with core lifecycle methods."""

    @property
    @abstractmethod
    def meta(self) -> "PluginMeta":
        """Plugin metadata descriptor"""
        pass

    @abstractmethod
    def init(self, settings: dict) -> None:
        """Initialize plugin with settings"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute plugin's main functionality"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup resources on shutdown"""
        pass

    def get_info(self) -> dict:
        """Get plugin info as dictionary"""
        return getattr(self, "meta", {}).as_dict()

    def load_config(self, plugin_dir: Optional[Path] = None) -> None:
        """Optional config loading from plugin_dir/config.toml"""
        pass

    def register_aiogram(self, router) -> None:
        """Optional aiogram handlers registration"""
        pass

    def register_fastapi(self, app) -> None:
        """Optional FastAPI routes registration"""
        pass

    def __str__(self) -> str:
        meta = getattr(self, "meta", None)
        if meta:
            return (
                f"{meta.name} v{meta.version} - {meta.description or 'No description'}"
            )
        return super().__str__()

    def __repr__(self) -> str:
        meta = getattr(self, "meta", None)
        if meta:
            return (
                f"<{self.__class__.__name__}(name={meta.name}, version={meta.version})>"
            )
        return super().__repr__()
