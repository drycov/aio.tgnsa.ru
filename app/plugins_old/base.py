import contextlib
import pathlib
from abc import ABC, abstractmethod
import sys
from typing import TYPE_CHECKING, List, Optional, Union

import tomli
from fastapi import APIRouter

if TYPE_CHECKING:
    from aiogram import Dispatcher
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from fastapi import FastAPI

import logging

# logger = logging.getLogger(__name__)
from app.core.config import logger


class Plugin(ABC):
    """
    Base interface for a plugin: supports priority, dependencies, versions, and registration.
    """

    name: str = "unnamed_plugin"
    description: str = "No description"
    priority: int = 100
    depends_on: List[str] = []
    config_class = None  # Optionally defined in the plugin

    router: Optional[APIRouter] = None
    dp: Optional["Dispatcher"] = None
    scheduler: Optional["AsyncIOScheduler"] = None
    _version: Optional[str] = None

    @abstractmethod
    def init(self, config: Optional[Union[dict, object]] = None) -> None:
        """
        Initializes the plugin.
        The config can be a dictionary or an object, depending on the specific plugin.
        """
        pass

    def register_fastapi(self, app: "FastAPI") -> None:
        """Registers FastAPI routes."""
        pass

    def register_aiogram(self, dp: "Dispatcher") -> None:
        """Registers aiogram handlers."""
        pass

    def register_scheduler(
        self, scheduler: Optional["AsyncIOScheduler"] = None
    ) -> None:
        """Registers tasks in APScheduler."""
        pass

    def get_version(self) -> str:
        """
        Retrieves the version of the plugin.

        The version is determined in the following order:
        1. If `_version` is set, it is returned.
        2. If a `VERSION` file exists in the plugin directory, its content is read.
        3. If a `pyproject.toml` file exists, the version is extracted from it.
        4. If none of the above, 'unknown' is returned.
        """
        if self._version:
            return self._version

        try:
            base_path = pathlib.Path(
                sys.modules[self.__class__.__module__].__file__
            ).parent
        except Exception as e:
            logger.warning(f"Failed to determine base path for plugin {self.name}: {e}")
            return "unknown"

        version_file = base_path / "VERSION"
        if version_file.is_file():
            try:
                self._version = version_file.read_text(encoding="utf-8").strip()
                return self._version
            except Exception as e:
                logger.warning(
                    f"Failed to read VERSION file for plugin {self.name}: {e}"
                )

        pyproject_path = base_path / "pyproject.toml"
        if pyproject_path.is_file():
            try:
                with pyproject_path.open("rb") as f:
                    toml_data = tomli.load(f)
                    self._version = (
                        toml_data.get("tool", {}).get("poetry", {}).get("version")
                    )
                    if self._version:
                        return self._version
            except Exception as e:
                logger.warning(
                    f"Failed to read pyproject.toml for plugin {self.name}: {e}"
                )
        return "unknown"

    def __repr__(self) -> str:
        return (
            f"<Plugin name='{self.name}', "
            f"version={self.get_version()}, "
            f"priority={self.priority}, "
            f"depends_on={self.depends_on}>"
        )

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if isinstance(other, Plugin):
            return self.name == other.name
        return False
