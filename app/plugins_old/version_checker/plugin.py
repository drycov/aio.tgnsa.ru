from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.plugins_old.base import Plugin
from app.core.plugin_manager import PluginManager
from app.core.config import settings, debug_mode


class VersionCheckerPlugin(Plugin):
    name = "version_checker"
    description = "Плагин для отображения версии API и подключённых плагинов"
    priority = 1

    def __init__(self):
        self.router = APIRouter()
        self._config = {}

    def init(self, config: dict = None) -> None:
        self._config = config or {}
        path = self._config.get("path", "/version")

        @self.router.get(path)
        async def version_summary():
            manager = PluginManager.get_instance()
            plugin_versions = (
                [
                    {
                        "name": plugin.name,
                        "description": plugin.description,
                        "version": plugin.get_version(),
                        "enabled": getattr(plugin, "enabled", True),
                        "priority": getattr(plugin, "priority", 100),
                    }
                    for plugin in manager.sorted_plugins
                ]
                if manager
                else []
            )

            return JSONResponse(
                {
                    "project": {
                        "name": settings.app.APP_NAME,
                        "description": settings.app.DESCRIPTION,
                        "version": settings.VERSION,
                        "debug": debug_mode,
                    },
                    "plugins": plugin_versions,
                }
            )

    def register_fastapi(self, app):
        app.include_router(self.router)


plugin = VersionCheckerPlugin()
