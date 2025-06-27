import socket
import psutil
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.plugins.base import Plugin


class NetstatUIPlugin(Plugin):
    name = "netstat_ui"
    description = "UI и API для просмотра сетевых сокетов"
    priority = 6

    def __init__(self):
        self.router = APIRouter()
        self._config = {}

        self.templates = Jinja2Templates(
            directory=str(Path(__file__).parent / "templates")
        )

    def init(self, config: dict):
        self._config = config or {}
        base_path = self._config.get("path", "/network/netstat")

        @self.router.get(f"{base_path}/json")
        async def netstat_json():
            connections = psutil.net_connections(kind="inet")
            data = []
            for conn in connections:
                try:
                    info = {
                        "protocol": "tcp" if conn.type == socket.SOCK_STREAM else "udp",
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "status": conn.status,
                        "pid": conn.pid,
                        "process": psutil.Process(conn.pid).name()
                        if conn.pid
                        else None,
                    }
                    data.append(info)
                except Exception:
                    continue
            return JSONResponse(data)

        @self.router.get(f"{base_path}/ui")
        async def netstat_ui(request: Request):
            return self.templates.TemplateResponse(
                "netstat_ui.html",
                {
                    "request": request,
                    "static_url": self._config.get("static_url", "/static"),
                    "favicon_url": self._config.get("favicon_url", "/favicon.ico"),
                },
            )

    def register_fastapi(self, app):
        app.include_router(self.router)


plugin = NetstatUIPlugin()
