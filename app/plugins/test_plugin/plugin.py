from typing import Optional
from fastapi import APIRouter
import logging

from app.core.plugin_manager.plugin_base import (
    PluginBase,
    PluginContext,
    PluginMetadata,
)

logger = logging.getLogger(__name__)


class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.meta = PluginMetadata(
            name="my_plugin",
            description="Demo plugin",
        )
        self.logger = logger
        self.router = None

    def _update_metadata_from_config(self, config: dict):
        plugin_cfg = config.get("plugin", {})
        for field in ("name", "description", "version", "author"):
            value = plugin_cfg.get(field)
            if value:
                setattr(self.meta, field, value)

    async def configure(self, context: PluginContext) -> None:
        self._update_metadata_from_config(context.settings or {})
        self.router = APIRouter()
        self.logger.debug(f"{self.meta.name}: configured")

    async def init(self, context: PluginContext) -> None:
        self.logger.info(f"{self.meta.name} v{self.meta.version or '-'} initialized")

    async def integrate(self, context: PluginContext) -> None:
        self.logger.info(f"{self.meta.name}: integrated")


plugin = MyPlugin()
