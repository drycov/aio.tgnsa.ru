from aiogram import Router
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramUnauthorizedError,
    TelegramForbiddenError,
    TelegramConflictError,
    TelegramNotFound,
    TelegramBadRequest,
    TelegramAPIError,
)
from aiogram.types import Update
from fastapi import HTTPException
from pydantic import ValidationError

from app.bot.constants.messages import ErrorMessages
from app.core.config import logger as app_logger

router = Router()


@router.errors()
async def error_handler(event: Update, *args, **kwargs):
    """
    Улучшенный обработчик ошибок Telegram API с:
    - Отловом ошибки "Invalid message argument"
    - Подробным логированием
    - Корректной обработкой ValidationError
    """
    exception = kwargs.get("exception")

    if not exception:
        app_logger.error(ErrorMessages.NO_EXCEPTION_INFO.value, exc_info=True)
        raise HTTPException(
            status_code=500, detail=ErrorMessages.UNKNOWN_ERROR_USER.value
        )

    # Обработка ошибки валидации сообщения
    if isinstance(exception, (ValidationError, TelegramBadRequest)):
        error_message = str(exception)

        # Специфическая обработка "Invalid message argument"
        if "Invalid message argument" in error_message:
            app_logger.warning(
                "Обнаружена ошибка валидации сообщения: %s",
                error_message,
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Ошибка форматирования сообщения. Пожалуйста, попробуйте другой запрос.",
            )

        # Остальные случаи BadRequest
        if isinstance(exception, TelegramBadRequest):
            if "blocked" in error_message.lower():
                app_logger.warning("Бот заблокирован пользователем.")
                raise HTTPException(
                    status_code=403, detail="Бот заблокирован пользователем"
                )
            elif "chat not found" in error_message.lower():
                app_logger.info("Чат с пользователем не найден.")
                raise HTTPException(
                    status_code=404, detail="Чат с пользователем не найден"
                )
            else:
                app_logger.warning(
                    ErrorMessages.BAD_REQUEST.value.format(exception=error_message)
                )
                raise HTTPException(
                    status_code=400,
                    detail=ErrorMessages.BAD_REQUEST.value.format(
                        exception=error_message
                    ),
                )

    # Стандартная обработка других ошибок Telegram API
    elif isinstance(exception, TelegramRetryAfter):
        retry_after = exception.retry_after
        app_logger.warning(
            ErrorMessages.FLOOD_CONTROL.value.format(retry_after=retry_after)
        )
        raise HTTPException(
            status_code=429,
            detail=ErrorMessages.FLOOD_CONTROL.value.format(retry_after=retry_after),
        )

    elif isinstance(exception, TelegramUnauthorizedError):
        app_logger.error(ErrorMessages.UNAUTHORIZED_TOKEN.value)
        raise HTTPException(
            status_code=401, detail=ErrorMessages.UNAUTHORIZED_TOKEN.value
        )

    elif isinstance(exception, TelegramForbiddenError):
        app_logger.warning(ErrorMessages.FORBIDDEN_CHAT.value)
        raise HTTPException(status_code=403, detail=ErrorMessages.FORBIDDEN_CHAT.value)

    elif isinstance(exception, TelegramConflictError):
        app_logger.error(ErrorMessages.TOKEN_CONFLICT.value)
        raise HTTPException(status_code=409, detail=ErrorMessages.TOKEN_CONFLICT.value)

    elif isinstance(exception, TelegramNotFound):
        app_logger.info(ErrorMessages.RESOURCE_NOT_FOUND.value)
        raise HTTPException(
            status_code=404, detail=ErrorMessages.RESOURCE_NOT_FOUND.value
        )

    elif isinstance(exception, TelegramAPIError):
        app_logger.error(
            ErrorMessages.TELEGRAM_API_ERROR.value.format(exception=exception)
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorMessages.TELEGRAM_API_ERROR.value.format(exception=exception),
        )

    else:
        # Обработка неизвестных ошибок
        app_logger.exception(ErrorMessages.UNKNOWN_ERROR_USER.value, exc_info=exception)
        raise HTTPException(
            status_code=500, detail=ErrorMessages.UNKNOWN_ERROR_USER.value
        )
