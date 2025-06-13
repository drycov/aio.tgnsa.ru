import traceback
from datetime import datetime

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import logger
from app.core.utils.date_utils import isotime


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": exc.errors(),
            "type": "validation_error"
        }
    )


async def http_error_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP ошибок."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": str(exc.detail),
            "type": "http_error"
        }
    )


async def general_error_handler(request: Request, exc: Exception):
    """Обработчик общих исключений."""
    logger.error(f"Необработанное исключение: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": "Внутренняя ошибка сервера",
            "type": "internal_error"
        }
    )
