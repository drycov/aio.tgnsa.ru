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

import logging

logger = logging.getLogger(__name__)

router = Router()


@router.errors()
async def error_handler(event: Update, *args, **kwargs):
    """
    Enhanced error handler for Telegram API errors with:
    - Catching "Invalid message argument" error
    - Detailed logging
    - Proper handling of ValidationError
    """
    exception = kwargs.get("exception")

    if not exception:
        logger.error(ErrorMessages.NO_EXCEPTION_INFO.value, exc_info=True)
        raise HTTPException(
            status_code=500, detail=ErrorMessages.UNKNOWN_ERROR_USER.value
        )

    # Handling message validation error
    if isinstance(exception, (ValidationError, TelegramBadRequest)):
        error_message = str(exception)

        # Specific handling for "Invalid message argument"
        if "Invalid message argument" in error_message:
            logger.warning(
                "Message validation error detected: %s",
                error_message,
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Message formatting error. Please try a different request.",
            )

        # Other BadRequest cases
        if isinstance(exception, TelegramBadRequest):
            if "blocked" in error_message.lower():
                logger.warning("Bot is blocked by the user.")
                raise HTTPException(
                    status_code=403, detail="Bot is blocked by the user"
                )
            elif "chat not found" in error_message.lower():
                logger.info("Chat with the user not found.")
                raise HTTPException(
                    status_code=404, detail="Chat with the user not found"
                )
            else:
                logger.warning(
                    ErrorMessages.BAD_REQUEST.value.format(exception=error_message)
                )
                raise HTTPException(
                    status_code=400,
                    detail=ErrorMessages.BAD_REQUEST.value.format(
                        exception=error_message
                    ),
                )

    # Standard handling for other Telegram API errors
    elif isinstance(exception, TelegramRetryAfter):
        retry_after = exception.retry_after
        logger.warning(
            ErrorMessages.FLOOD_CONTROL.value.format(retry_after=retry_after)
        )
        raise HTTPException(
            status_code=429,
            detail=ErrorMessages.FLOOD_CONTROL.value.format(retry_after=retry_after),
        )

    elif isinstance(exception, TelegramUnauthorizedError):
        logger.error(ErrorMessages.UNAUTHORIZED_TOKEN.value)
        raise HTTPException(
            status_code=401, detail=ErrorMessages.UNAUTHORIZED_TOKEN.value
        )

    elif isinstance(exception, TelegramForbiddenError):
        logger.warning(ErrorMessages.FORBIDDEN_CHAT.value)
        raise HTTPException(status_code=403, detail=ErrorMessages.FORBIDDEN_CHAT.value)

    elif isinstance(exception, TelegramConflictError):
        logger.error(ErrorMessages.TOKEN_CONFLICT.value)
        raise HTTPException(status_code=409, detail=ErrorMessages.TOKEN_CONFLICT.value)

    elif isinstance(exception, TelegramNotFound):
        logger.info(ErrorMessages.RESOURCE_NOT_FOUND.value)
        raise HTTPException(
            status_code=404, detail=ErrorMessages.RESOURCE_NOT_FOUND.value
        )

    elif isinstance(exception, TelegramAPIError):
        logger.error(
            ErrorMessages.TELEGRAM_API_ERROR.value.format(exception=exception)
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorMessages.TELEGRAM_API_ERROR.value.format(exception=exception),
        )

    elif "TelegramNetworkError" in str(exception) or "ClientConnectorDNSError" in str(
        exception
    ):
        logger.error(f"Network error: {exception}")
        raise HTTPException(
            status_code=503,
            detail="Сетевая ошибка Telegram API. Проверьте соединение с api.telegram.org.",
        )

    else:
        # Handling unknown errors
        logger.exception(ErrorMessages.UNKNOWN_ERROR_USER.value, exc_info=exception)
        raise HTTPException(
            status_code=500, detail=ErrorMessages.UNKNOWN_ERROR_USER.value
        )
