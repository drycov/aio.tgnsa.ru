import traceback
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import logger
from app.core.utils.date_utils import isotime


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handles request validation errors.

    Overrides the default 422 case:
      - Returns a structured JSON response with a `detail` field
      - Message format:
        {
          "status": "error",
          "timestamp": "...",
          "path": "/...",
          "method": "POST",
          "detail": [...],
          "type": "validation_error"
        }

    Connected via FastAPI: app.exception_handler(RequestValidationError)
    """
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
    """
    Handles HTTP exceptions.

    Catches Starlette HTTPException (including FastAPI HTTPException),
    and returns a JSON response with details.
    Connected via: app.exception_handler(HTTPException)
    """
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
    """
    Handles unhandled exceptions.

    Logs the stack trace and exception, returns a 500 Internal Server Error
    with a generic message, without leaking details.
    Connected via: app.exception_handler(Exception)
    """
    logger.error(f"Unhandled exception for {request.method} {request.url.path}: {exc}")
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
