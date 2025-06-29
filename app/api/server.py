import re
from typing import List, Pattern

from app import __version__
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.api.middlewares.middleware import RequestLoggingMiddleware
from app.api.routes import api_router
from app.core.applcm_manager import AppLifecycleManager
from app.core.config import debug_mode, logger, settings
from app.core.errors import (
    general_error_handler,
    http_error_handler,
    validation_error_handler,
)
from app.core.patchs import ProjectPaths
from app.core.plugin_manager import PluginManager

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


class ApiManager:
    def __init__(self, lifecycle_manager: AppLifecycleManager):
        self.lifecycle_manager = lifecycle_manager

        self.app: FastAPI = FastAPI(
            title=settings.app.APP_NAME,
            version=__version__,
        )
        self._setup_static()
        self._setup_middleware()
        self._setup_exception_handlers()
        self._setup_routes()
        self._setup_plugins()

        self.lifecycle_manager.on_startup(name="api_startup")(self.on_startup)
        self.lifecycle_manager.on_shutdown(name="api_shutdown")(self.on_shutdown)

        # Также можно зарегистрировать события FastAPI
        self.app.add_event_handler("startup", self.on_startup)
        self.app.add_event_handler("shutdown", self.on_shutdown)

    def _setup_static(self):
        paths = ProjectPaths()
        logger.debug(f"Настройка статических файлов: {paths.static_dir}")
        self.app.mount(
            settings.app.STATIC_URL,
            StaticFiles(directory=str(paths.static_dir)),
            name="static",
        )

    def _setup_middleware(self):
        logger.debug("Настройка middleware")
        self.app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=EXCLUDE_PATHS,
            exclude_patterns=EXCLUDE_PATTERNS,
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # В продакшне сузить список
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_exception_handlers(self):
        self.app.add_exception_handler(RequestValidationError, validation_error_handler)
        self.app.add_exception_handler(HTTPException, http_error_handler)
        self.app.add_exception_handler(Exception, general_error_handler)

    def _setup_routes(self):
        self.app.include_router(api_router)

    def _setup_plugins(self):
        manager = PluginManager.create_once()
        manager.load_all()
        manager.init_all(settings)
        manager.post_init_integration()
        manager.register_fastapi(self.app)

    def get_app(self) -> FastAPI:
        return self.app

        # Пример методов-хуков, которые будут вызваны при старте и остановке

    async def on_startup(self):
        logger.info("🟢 Запуск API... Инициализация ресурсов.")
        # Здесь может быть инициализация БД, кешей и прочего
        # await some_async_init()

    async def on_shutdown(self):
        logger.info("🛑 Завершение работы API... Освобождение ресурсов.")
        # Очистка ресурсов, закрытие соединений
        # await some_async_cleanup()


def start_api(lifecycle: AppLifecycleManager) -> None:
    """
    Инициализация ApiManager и запуск uvicorn сервера.
    """
    api_manager = ApiManager(lifecycle)
    app = api_manager.get_app()

    uvicorn.run(
        app,
        host=settings.api.API_HOST,
        port=settings.api.API_PORT,
        workers=1 if debug_mode else settings.api.API_WORKERS,
        reload=debug_mode,
        log_level="debug" if debug_mode else "info",
    )


# def setup_plugins(app: FastAPI):
#     manager = PluginManager.create_once()
#     manager.load_all()
#     manager.init_all(settings)
#     manager.post_init_integration()
#     manager.register_fastapi(app)


# def create_app() -> FastAPI:
#     """
#     Создает и конфигурирует экземпляр FastAPI приложения.

#     Returns:
#         FastAPI: сконфигурированное приложение
#     """
#     app = FastAPI()
#     app.title = settings.app.APP_NAME
#     app.version = __version__

#     # Настройка статических файлов
#     paths = ProjectPaths()
#     logger.debug(f"Настройка статических файлов: {paths.static_dir}")
#     app.mount(
#         settings.app.STATIC_URL,
#         StaticFiles(directory=str(paths.static_dir)),
#         name="static",
#     )

#     # Настройка middleware
#     logger.debug("Настройка middleware")

#     app.add_middleware(
#         RequestLoggingMiddleware,
#         exclude_paths=EXCLUDE_PATHS,
#         exclude_patterns=EXCLUDE_PATTERNS,
#     )

#     app.add_middleware(
#         CORSMiddleware,
#         # В продакшне желательно ограничить конкретными доменами
#         allow_origins=["*"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

#     # Регистрация обработчиков ошибок
#     app.add_exception_handler(RequestValidationError, validation_error_handler)
#     app.add_exception_handler(HTTPException, http_error_handler)
#     app.add_exception_handler(Exception, general_error_handler)

#     # Роутинг
#     app.include_router(api_router)

#     setup_plugins(app)

#     return app


# app = create_app()


# def run_api() -> None:
#     """
#     Запускает uvicorn сервер с настройками из конфигурации.
#     """
#     host = settings.api.API_HOST
#     port = settings.api.API_PORT
#     workers = 1 if debug_mode else settings.api.API_WORKERS

#     logger.info(
#         f"🌐 Запуск API-сервера на {host}:{port} "
#         f"(режим: {'отладка' if debug_mode else 'продакшн'}, "
#         f"число воркеров: {workers})..."
#     )

#     uvicorn.run(
#         "app.api.server:app",
#         host=host,
#         port=port,
#         workers=workers,
#         reload=debug_mode,  # Включить авто-перезагрузку только в режиме отладки
#         log_level="debug" if debug_mode else "info",
#     )
