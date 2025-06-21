import re
from typing import List, Pattern

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.api.middlewares.middleware import RequestLoggingMiddleware
from app.api.routes import api_router
from app.core.config import debug_mode, logger, settings
from app.core.errors import (general_error_handler, http_error_handler,
                             validation_error_handler)
from app.core.patchs import ProjectPaths
from app.plugins.manager import PluginManager

EXCLUDE_PATHS: List[str] = [
    "/",
    "/metrics",
    "/favicon.ico",
]

EXCLUDE_PATTERNS: List[Pattern] = [
    re.compile(r"^/static/.*"),
    re.compile(r"^/docs/?$"),
    re.compile(r"^/redoc/?$"),
    re.compile(r"^/openapi.json$"),
    re.compile(r"^/api/system-info$"),
]



def setup_plugins(app: FastAPI):
    manager = PluginManager.create_once()
    manager.load_all()
    manager.init_all(settings)
    manager.register_fastapi(app)

def create_app() -> FastAPI:
    """
    Создает и конфигурирует экземпляр FastAPI приложения.

    Returns:
        FastAPI: сконфигурированное приложение
    """
    app = FastAPI()

    # Настройка статических файлов
    paths = ProjectPaths()
    logger.debug(f"Настройка статических файлов: {paths.static_dir}")
    app.mount(
        settings.app.STATIC_URL,
        StaticFiles(directory=str(paths.static_dir)),
        name="static"
    )

    # Настройка middleware
    logger.debug("Настройка middleware")

    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=EXCLUDE_PATHS,
        exclude_patterns=EXCLUDE_PATTERNS
    )

    app.add_middleware(
        CORSMiddleware,
        # В продакшне желательно ограничить конкретными доменами
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Регистрация обработчиков ошибок
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, general_error_handler)

    # Роутинг
    app.include_router(api_router)
    
    setup_plugins(app)

    return app


app = create_app()


def run_api() -> None:
    """
    Запускает uvicorn сервер с настройками из конфигурации.
    """
    host = settings.api.API_HOST
    port = settings.api.API_PORT
    workers = 1 if debug_mode else settings.api.API_WORKERS

    logger.info(
        f"🌐 Запуск API-сервера на {host}:{port} "
        f"(режим: {'отладка' if debug_mode else 'продакшн'}, "
        f"число воркеров: {workers})..."
    )

    uvicorn.run(
        "app.api.server:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug_mode,  # Включить авто-перезагрузку только в режиме отладки
        log_level="debug" if debug_mode else "info",
    )
