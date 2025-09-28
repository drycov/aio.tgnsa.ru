from abc import ABC, abstractmethod
from typing import Dict, Type, Any


class IPluginSource(ABC):
    """
    Интерфейс для источников плагинов.
    Определяет методы для загрузки и получения плагинов.
    """

    @abstractmethod
    def load_plugins(self) -> Dict[str, Any]:
        """Загружает плагины из источника и возвращает их в виде словаря."""
        pass

    @abstractmethod
    def plugins(self) -> Dict[str, Type]:
        """Возвращает уже загруженные плагины."""
        pass
