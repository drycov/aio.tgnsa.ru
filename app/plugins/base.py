import contextlib
import pathlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Union

import tomli
from fastapi import APIRouter

if TYPE_CHECKING:
    from aiogram import Dispatcher
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from fastapi import FastAPI


class Plugin(ABC):
    """
    Базовый интерфейс плагина: поддержка приоритета, зависимостей, версий и регистрации.
    """

    name: str = "unnamed_plugin"
    description: str = "No description"
    priority: int = 100
    depends_on: List[str] = []
    config_class = None  # Опционально, может быть задана в плагине

    router: Optional[APIRouter] = None
    dp: Optional["Dispatcher"] = None
    scheduler: Optional["AsyncIOScheduler"] = None
    _version: Optional[str] = None

    @abstractmethod
    def init(self, config: Optional[Union[dict, object]] = None) -> None:
        """
        Инициализация плагина.
        Конфиг может быть словарём или объектом — зависит от конкретного плагина.
        """
        pass

    def register_fastapi(self, app: "FastAPI") -> None:
        """Регистрация маршрутов FastAPI."""
        pass

    def register_aiogram(self, dp: "Dispatcher") -> None:
        """Регистрация aiogram-хендлеров."""
        pass

    def register_scheduler(self, scheduler: Optional["AsyncIOScheduler"] = None) -> None:
        """Регистрация задач в APScheduler."""
        pass

    def get_version(self) -> str:
        """
        Определение версии:
        - `plugins/<name>/VERSION`
        - `plugins/<name>/pyproject.toml`
        - fallback: "unknown"
        """
        if self._version:
            return self._version

        base_path = pathlib.Path(__file__).parent.parent / "plugins" / self.name

        version_file = base_path / "VERSION"
        if version_file.is_file():
            self._version = version_file.read_text(encoding="utf-8").strip()
            return self._version

        pyproject_path = base_path / "pyproject.toml"
        if pyproject_path.is_file():
            with contextlib.suppress(Exception):
                with pyproject_path.open("rb") as f:
                    toml_data = tomli.load(f)
                    self._version = toml_data.get("tool", {}).get("poetry", {}).get("version")
                    if self._version:
                        return self._version

        return "unknown"

    def __repr__(self) -> str:
        return f"<Plugin name={self.name!r}, version={self.get_version()}, priority={self.priority}, depends_on={self.depends_on}>"

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return self.name == other