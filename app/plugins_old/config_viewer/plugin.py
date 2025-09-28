from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.plugins_old.base import Plugin
from app.core.config import settings

TEMPLATE_DIR = Path(__file__).parent / "templates"


class ConfigViewerPlugin(Plugin):
    name = "config_viewer"
    description = "Web UI for viewing current configuration"
    priority = 10

    def __init__(self):
        self.router = APIRouter()
        self._config = {}
        self.templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

    def init(self, config: dict):
        self._config = config or {}
        path = self._config.get("path", "/config")

        @self.router.get(path, response_class=HTMLResponse)
        async def view_config(request: Request):
            return self.templates.TemplateResponse(
                "config_viewer.html",
                {
                    "request": request,
                    "config": settings.model_dump(mode="json"),
                    "static_url": self._config.get("static_url", "/static"),
                    "favicon_url": self._config.get("favicon_url", "/favicon.ico"),
                },
            )

    def register_fastapi(self, app):
        app.include_router(
            self.router,
        )


plugin = ConfigViewerPlugin()
