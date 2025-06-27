import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from inspect import isclass

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.types import ASGIApp

from app.core.config import logger
from app.plugins.base import Plugin


class MiddlewareViewerPlugin(Plugin):
    name = "middleware_viewer"
    description = "Просмотр и анализ зарегистрированных middleware FastAPI"
    priority = 10  # Средний приоритет загрузки

    def __init__(self):
        self.router = APIRouter()
        self.templates: Optional[Jinja2Templates] = None
        self._config: Dict[str, Any] = {}
        self.logger = logger
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Инициализация маршрутов FastAPI."""
        base_path = self._config.get("path", "/middleware")
        self.router.add_api_route(
            path=f"{base_path}",
            endpoint=self.view_middlewares,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
            name="middleware_viewer",
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

    async def view_middlewares(self, request: Request) -> HTMLResponse:
        """Отображение списка зарегистрированных middleware."""
        app = request.app

        if not hasattr(app, "user_middleware"):
            raise HTTPException(
                status_code=500, detail="FastAPI middleware information not available"
            )

        middleware_list = self._analyze_middlewares(app)

        return self.templates.TemplateResponse(
            "middleware_viewer.html",
            {
                "request": request,
                "middlewares": middleware_list,
                "title": "Middleware Inspector",
                "static_url": self._config.get("static_url", "/static"),
                "favicon_url": self._config.get("favicon_url", "/favicon.ico"),
                "total_count": len(middleware_list),
                "app_name": getattr(app, "title", "FastAPI Application"),
            },
        )

    def _analyze_middlewares(self, app: ASGIApp) -> List[Dict[str, Any]]:
        """Анализ и сбор информации о middleware с улучшенной обработкой ошибок."""
        middlewares = []

        for idx, mw in enumerate(getattr(app, "user_middleware", []), 1):
            try:
                middleware_info = {
                    "id": idx,
                    "class": self._get_middleware_class_info(mw.cls),
                    "options": self._safe_get_options(mw),
                    "order": idx,
                    "is_coroutine": self._is_coroutine_middleware(mw.cls),
                    "type": mw.type if hasattr(mw, "type") else "unknown",
                }

                # Добавляем дополнительную информацию для строковых middleware
                if isinstance(mw.cls, str):
                    middleware_info["import_path"] = mw.cls

                middlewares.append(middleware_info)
            except Exception as ex:
                self.logger.error(
                    f"Error analyzing middleware {idx}: {ex!r}",
                    exc_info=logger.level <= logging.DEBUG,
                )
                middlewares.append({"id": idx, "error": str(ex), "raw_data": str(mw)})

        return middlewares

    def _get_middleware_class_info(self, mw_cls: Any) -> Dict[str, str]:
        """Получение информации о классе middleware с обработкой строковых middleware."""
        if isinstance(mw_cls, str):
            # Обработка строковых middleware (например, 'app.middleware.some_middleware')
            return {
                "name": mw_cls.split(".")[-1],
                "module": ".".join(mw_cls.split(".")[:-1]),
                "doc": "String path to middleware",
                "type": "string_reference",
            }
        elif isclass(mw_cls):
            return {
                "name": mw_cls.__name__,
                "module": mw_cls.__module__,
                "doc": (mw_cls.__doc__ or "").strip(),
                "type": "class",
            }
        elif callable(mw_cls):
            return {
                "name": getattr(mw_cls, "__name__", "anonymous_function"),
                "module": getattr(mw_cls, "__module__", "unknown"),
                "doc": (getattr(mw_cls, "__doc__", "") or "").strip(),
                "type": "function",
            }
        return {"name": str(mw_cls), "module": "unknown", "doc": "", "type": "unknown"}

    def _safe_get_options(self, mw: Any) -> Dict[str, Any]:
        """Безопасное получение и сериализация опций middleware."""
        try:
            raw_kwargs = getattr(mw, "kwargs", {}).copy()
            try:
                # Пытаемся сериализовать каждый элемент отдельно
                return json.loads(json.dumps(raw_kwargs, default=str))
            except Exception as e:
                self.logger.warning(f"Middleware kwargs serialization failed: {e}")
                return {"error": "Unserializable middleware options"}
        except Exception:
            return {}

    def _is_coroutine_middleware(self, mw_cls: Any) -> Optional[bool]:
        """Проверка, является ли middleware корутиной с безопасной обработкой."""
        if isinstance(mw_cls, str):
            # Не можем определить для строкового пути
            return None
        if not callable(mw_cls):
            return False

        try:
            if isclass(mw_cls):
                for method in vars(mw_cls).values():
                    if (
                        method.__name__ == "__call__"
                        and getattr(method, "__code__", None)
                        and method.__code__.co_flags & 0x80
                    ):
                        return True
            elif hasattr(mw_cls, "__code__"):
                return bool(mw_cls.__code__.co_flags & 0x80)
        except Exception as e:
            logger.debug(f"Could not determine coroutine status: {e}")

        return False

    def register_fastapi(self, app: ASGIApp) -> None:
        """Регистрация маршрутов в FastAPI."""
        base_path = self._config.get("path", "/middleware")
        app.include_router(self.router, prefix=base_path, tags=["middleware_inspector"])


plugin = MiddlewareViewerPlugin()
