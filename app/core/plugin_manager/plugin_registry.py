from typing import List, Optional
import logging
import asyncio

from .plugin_base import PluginBase, Reloadable, Stoppable

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Централизованный реестр для управления плагинами.
    """

    _plugins: List[PluginBase] = []

    @classmethod
    def register(cls, plugin: PluginBase) -> None:
        if plugin not in cls._plugins:
            cls._plugins.append(plugin)
            name = getattr(plugin.meta, "name", plugin.__class__.__name__)
            logger.debug(f"Plugin registered: {name}")
        else:
            logger.debug(
                f"Plugin already registered: {getattr(plugin.meta, 'name', plugin.__class__.__name__)}"
            )

    @classmethod
    def get_all(cls) -> List[PluginBase]:
        return cls._plugins.copy()

    @classmethod
    def get_by_name(cls, name: str) -> Optional[PluginBase]:
        for plugin in cls._plugins:
            if getattr(plugin.meta, "name", None) == name:
                return plugin
        return None

    @classmethod
    def clear(cls) -> None:
        cls._plugins.clear()
        logger.debug("All plugins cleared from the registry")

    @classmethod
    async def shutdown_all(cls) -> None:
        tasks = []
        for plugin in cls._plugins:
            if isinstance(plugin, Stoppable):
                tasks.append(cls._safe_call(plugin.shutdown, plugin))
        if tasks:
            await asyncio.gather(*tasks)

    @classmethod
    async def reload_all(cls) -> None:
        tasks = []
        for plugin in cls._plugins:
            if isinstance(plugin, Reloadable):
                tasks.append(cls._safe_call(plugin.reload, plugin))
        if tasks:
            await asyncio.gather(*tasks)

    @staticmethod
    async def _safe_call(coro, plugin):
        try:
            await coro()
            logger.info(
                f"Plugin operation succeeded: {getattr(plugin.meta, 'name', plugin.__class__.__name__)}"
            )
        except Exception as e:
            logger.error(
                f"Error during plugin operation on {getattr(plugin.meta, 'name', plugin.__class__.__name__)}: {e}"
            )
