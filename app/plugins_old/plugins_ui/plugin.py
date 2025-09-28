from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Dict, Any, List
import tomllib

from app.plugins_old.base import Plugin
from app.core.config import logger
from app.core.plugin_manager import PluginManager


class PluginsUIPlugin(Plugin):
    name = "plugins_ui"
    description = "Web-интерфейс для управления плагинами"
    priority = 0  # Высший приоритет для загрузки первым

    def __init__(self):
        self.router = APIRouter()
        self._config: Dict[str, Any] = {}
        self.templates: Jinja2Templates = None
        path = self._config.get("path", "/plugins")
        self._setup_routes(path)

    def _setup_routes(self, base_path: str) -> None:
        """Инициализация маршрутов FastAPI."""
        self.router.add_api_route(
            path=f"{base_path}/",
            endpoint=self._plugins_ui_view,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=True,
        )
        self.router.add_api_route(
            path=f"{base_path}/enable/{{plugin_name}}",
            endpoint=self._enable_plugin,
            methods=["POST"],
            response_class=JSONResponse,
        )
        self.router.add_api_route(
            path=f"{base_path}/disable/{{plugin_name}}",
            endpoint=self._disable_plugin,
            methods=["POST"],
            response_class=JSONResponse,
        )

    def init(self, config: Dict[str, Any]) -> None:
        """Инициализация плагина с конфигурацией."""
        self._config = config or {}
        templates_dir = Path(
            self._config.get("templates_dir", Path(__file__).parent / "templates")
        )

        try:
            self.templates = Jinja2Templates(directory=str(templates_dir))
        except Exception as e:
            logger.error(f"Failed to initialize templates: {e}")
            raise RuntimeError("Could not initialize templates directory") from e

    async def _plugins_ui_view(self, request: Request) -> HTMLResponse:
        """Отображение веб-интерфейса плагинов."""
        plugin_manager = PluginManager.get_instance()
        if not plugin_manager:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PluginManager not initialized",
            )

        plugins_data = self._get_plugins_data(plugin_manager)
        base_path = self._config.get("path", "/plugins")

        return self.templates.TemplateResponse(
            "plugins_ui.html",
            {
                "request": request,
                "plugins": plugins_data,
                "static_url": self._config.get("static_url", "/static"),
                "favicon_url": self._config.get("favicon_url", "/favicon.ico"),
                "base_path": base_path,
                "title": "Управление плагинами",
            },
        )

    def _get_plugins_data(self, plugin_manager: PluginManager) -> List[Dict[str, Any]]:
        """Получение данных о плагинах для отображения."""
        return [
            {
                "name": plugin.name,
                "desc": plugin.description,
                "enabled": getattr(plugin, "enabled", True),
                "priority": getattr(plugin, "priority", 100),
                "depends_on": getattr(plugin, "depends_on", []),
                "configurable": hasattr(plugin, "config_class"),
            }
            for plugin in plugin_manager.sorted_plugins
        ]

    async def _enable_plugin(self, plugin_name: str, request: Request) -> JSONResponse:
        """Включение плагина."""
        return await self._toggle_plugin(plugin_name, True, request)

    async def _disable_plugin(self, plugin_name: str, request: Request) -> JSONResponse:
        """Отключение плагина."""
        return await self._toggle_plugin(plugin_name, False, request)

    async def _toggle_plugin(
        self, plugin_name: str, enabled: bool, request: Request
    ) -> JSONResponse:
        """Общая логика включения/отключения плагина."""
        plugin_manager = PluginManager.get_instance()
        if not plugin_manager:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Plugin manager not initialized",
            )

        if plugin_name not in plugin_manager.plugins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_name}' not found",
            )

        try:
            current_config = self._load_current_config(plugin_manager)
            self._update_plugin_config(plugin_name, enabled, current_config)
            plugin_manager.plugin_configs = current_config

            app = request.app
            success = plugin_manager.reload_plugin(
                plugin_name,
                app=app,
                dp=getattr(app.state, "dp", None),
                scheduler=getattr(app.state, "scheduler", None),
            )

            return JSONResponse(
                {
                    "status": "success",
                    "plugin": plugin_name,
                    "enabled": enabled,
                    "reloaded": success,
                    "message": f"Plugin '{plugin_name}' {'enabled' if enabled else 'disabled'}",
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to toggle plugin {plugin_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update plugin state: {str(e)}",
            ) from e

    def _load_current_config(self, plugin_manager: PluginManager) -> Dict[str, Any]:
        """Загрузка текущей конфигурации плагинов."""
        if not plugin_manager.plugin_config_file.exists():
            return {}

        try:
            with plugin_manager.plugin_config_file.open("rb") as f:
                return tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to load plugin config: {e}")
            raise RuntimeError("Could not load plugin configuration") from e

    def _update_plugin_config(
        self, plugin_name: str, enabled: bool, config: Dict[str, Any]
    ) -> None:
        """Обновление конфигурации плагина."""
        plugin_config = config.get(plugin_name, {})
        plugin_config["enabled"] = enabled
        config[plugin_name] = plugin_config

        try:
            PluginManager.get_instance().atomic_write(
                PluginManager.get_instance().plugin_config_file, config
            )
        except Exception as e:
            logger.error(f"Failed to write plugin config: {e}")
            raise RuntimeError("Could not save plugin configuration") from e

    def register_fastapi(self, app) -> None:
        """Регистрация маршрутов в FastAPI."""
        app.include_router(self.router)


plugin = PluginsUIPlugin()
