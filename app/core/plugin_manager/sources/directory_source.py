from pathlib import Path
import importlib.util
import sys
from types import ModuleType
from typing import Any, Dict, Optional, Type

from app.core.plugin_manager.base import PluginBase
from app.core.plugin_manager.interfaces import IPluginSource
from app.core.config import logger


class PluginDirectorySource(IPluginSource):
    def __init__(self, path: Path, base_class: Optional[Type] = None):
        self.path = path
        self.base_class = base_class
        self.plugins: Dict[str, PluginBase] = {}
        self._logger = logger.bind(source="PluginDirectorySource")

    def load_plugins(self) -> Dict[str, PluginBase]:
        """
        Загружает все плагины из поддиректорий с `plugin.py` или `__init__.py`.
        """
        self.plugins.clear()
        if not self.path.exists() or not self.path.is_dir():
            self._logger.warning(f"📁 Папка с плагинами не найдена: {self.path}")
            return {}

        self._logger.debug(f"🔍 Сканируем директорию плагинов: {self.path}")
        plugin_type = self._detect_plugin_type()
        sys.path.insert(0, str(self.path))

        try:
            for entry in self.path.iterdir():
                if not entry.is_dir() or entry.name.startswith("_"):
                    continue

                plugin_file = entry / "plugin.py"
                init_file = entry / "__init__.py"

                if plugin_file.exists():
                    module_name = f"{self.path.name}.{entry.name}.plugin"
                    file_path = plugin_file
                elif init_file.exists():
                    module_name = entry.name
                    file_path = init_file
                else:
                    self._logger.debug(
                        f"⏭️ Пропущен {entry}: нет plugin.py или __init__.py"
                    )
                    continue

                plugin = self._load_plugin(module_name, file_path, entry)
                if plugin:
                    setattr(plugin, "plugin_type", plugin_type)
                    setattr(plugin, "plugin_dir", entry)
                    self.plugins[plugin.name] = plugin

        finally:
            sys.path.pop(0)

        self._logger.info(
            f"📦 Загружено плагинов: {len(self.plugins)} (тип: {plugin_type})"
        )
        return self.plugins

    def _load_plugin(
        self, module_name: str, file_path: Path, plugin_dir: Path
    ) -> Optional[PluginBase]:
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                self._logger.warning(f"⚠️ Spec не создан для: {module_name}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return self._extract_plugin(module, module_name)

        except Exception as e:
            self._logger.exception(f"❌ Ошибка загрузки модуля '{module_name}': {e}")
            return None

    def _extract_plugin(
        self, module: ModuleType, module_name: str
    ) -> Optional[PluginBase]:
        self._logger.debug(f"🔍 Извлекаем плагины из модуля: {module_name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if not isinstance(attr, type) or not attr.__module__.startswith(
                module.__name__
            ):
                continue

            if self.base_class:
                if not issubclass(attr, self.base_class):
                    self._logger.debug(
                        f"⏭️ '{attr.__name__}' не является подклассом '{self.base_class.__name__}'"
                    )
                    continue
                if attr is self.base_class:
                    continue

            try:
                instance = attr()
                self._logger.info(
                    f"✅ Плагин '{module_name}' ({attr.__name__}) загружен"
                )
                return instance
            except Exception as e:
                self._logger.error(
                    f"❌ Не удалось создать экземпляр '{attr.__name__}': {e}"
                )
        return None

    def _detect_plugin_type(self) -> str:
        path_str = str(self.path).replace("\\", "/").lower()
        if "core/plugins" in path_str:
            return "core"
        if "app/plugins" in path_str:
            return "app"
        return "external"

    def plugins(self) -> Dict[str, PluginBase]:
        """Совместимость с интерфейсом IPluginSource."""
        return self.load_plugins()
