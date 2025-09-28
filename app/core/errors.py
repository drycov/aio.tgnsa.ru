import traceback
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from app.core.logging_setup import logger  # ✅ Исправление
from app.core.utils.date_utils import isotime
from app.core.utils.decorators import log_execution


@log_execution(
    level="info",
    success_message="Ошибка валидации корректно обработана.",
    error_message="Ошибка валидации конфигурации",
    log_args=False,
    log_exceptions=False,  # ✅ Не дублируем лог ниже
)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.error(
        f"Validation error for {request.method} {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": exc.errors(),
            "type": "validation_error",
        },
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.error(
        f"HTTP error for {request.method} {request.url.path}: {exc.status_code} {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": str(exc.detail),
            "type": "http_error",
        },
    )


async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled exception for {request.method} {request.url.path}: {exc}"
    )
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": "Internal Server Error",
            "type": "internal_error",
        },
    )


class PluginError(Exception):
    """
    Исключение для ошибок, связанных с плагинами.
    Используется для явного обозначения ошибок в жизненном цикле плагинов.
    """

    def __init__(self, message: str, *, plugin: str = None):
        self.plugin = plugin
        super().__init__(f"[Plugin: {plugin}] {message}" if plugin else message)
