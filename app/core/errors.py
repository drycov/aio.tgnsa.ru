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
    Обработчик ошибок валидации запроса.

    Переопределяет стандартный кейс 422:
      - Возвращает структурированную JSON-ответ с полем `detail`
      - Формат сообщения:
        {
          "status": "error",
          "timestamp": "...",
          "path": "/... ",
          "method": "POST",
          "detail": [...],
          "type": "validation_error"
        }

    Подключается через FastAPI: app.exception_handler(RequestValidationError)
    :contentReference[oaicite:1]{index=1}
    """
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
    Обработчик HTTP-исключений.

    Перехватывает Starlette HTTPException (включая FastAPI HTTPException),
    возвращает JSON с деталями.
    Подключается: app.exception_handler(HTTPException)
    :contentReference[oaicite:2]{index=2}
    """
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
    Обработчик необработанных исключений.

    Логирует стек и исключение, возвращает 500 Internal Server Error
    с обобщённым сообщением, без утечки деталей.
    Подключается: app.exception_handler(Exception)
    :contentReference[oaicite:3]{index=3}
    """
    # Логируем ошибку и стек
    logger.error(f"Необработанное исключение: {exc}")
    logger.error(traceback.format_exc())

    # Возвращаем обобщённый ответ
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "timestamp": isotime(),
            "path": request.url.path,
            "method": request.method,
            "detail": "Внутренняя ошибка сервера",
            "type": "internal_error",
        },
    )
