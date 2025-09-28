# app/core/plugin_manager/sources/module_source.py

from typing import Dict, Any, Optional, Type
import importlib
import inspect

from app.core.plugin_manager.interfaces import IPluginSource
from app.core.plugin_manager.base import PluginBase
from app.core.config import logger


class ModulePluginSource(IPluginSource):
    """
    Источник плагинов, загружающий их из указанных модулей по dotted path.
    """

    def __init__(self, modules: list[str], base_class: Optional[Type] = None):
        self.modules = modules
        self.base_class = base_class or PluginBase
        self._logger = logger.bind(source="module_plugin_source")

    def load_plugins(self) -> Dict[str, PluginBase]:
        plugins: Dict[str, PluginBase] = {}

        for module_path in self.modules:
            try:
                module = importlib.import_module(module_path)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, self.base_class)
                        and attr is not self.base_class
                    ):
                        instance = attr()
                        plugin_name = getattr(instance.meta, "name", attr.__name__)
                        plugins[plugin_name] = instance
                        self._logger.info(
                            f"✅ Loaded plugin: {plugin_name} from {module_path}"
                        )

            except Exception as e:
                self._logger.error(
                    f"❌ Failed to import plugin module '{module_path}': {e}",
                    exc_info=True,
                )

        return plugins

    def plugins(self):
        return self.load_plugins()
