from aiogram import Router
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramUnauthorizedError,
    TelegramForbiddenError,
    TelegramConflictError,
    TelegramNotFound,
    TelegramBadRequest,
    TelegramAPIError,
    TelegramNetworkError,
)
from aiogram.types import Update
from fastapi import HTTPException
from pydantic import ValidationError

from app.bot.constants.messages import ErrorMessages
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.errors()
async def error_handler(event: Update, exception: Exception):
    """
    Centralized error handler for Aiogram + FastAPI.
    Maps known Telegram/Pydantic errors to HTTPException,
    logs everything else.
    """

    # Validation / BadRequest
    if isinstance(exception, (ValidationError, TelegramBadRequest)):
        error_message = str(exception)

        if "Invalid message argument" in error_message:
            logger.warning("Message validation error: %s", error_message)
            raise HTTPException(status_code=400, detail="Ошибка форматирования сообщения.")

        if isinstance(exception, TelegramBadRequest):
            if "blocked" in error_message.lower():
                logger.warning("Bot is blocked by user.")
                raise HTTPException(status_code=403, detail="Bot is blocked by user")
            elif "chat not found" in error_message.lower():
                logger.info("Chat not found.")
                raise HTTPException(status_code=404, detail="Chat not found")
            else:
                logger.warning(f"BadRequest: {error_message}")
                raise HTTPException(status_code=400, detail=f"BadRequest: {error_message}")

    elif isinstance(exception, TelegramRetryAfter):
        logger.warning(f"Flood control: retry after {exception.retry_after}s")
        raise HTTPException(status_code=429, detail=f"Flood control: retry after {exception.retry_after}s")

    elif isinstance(exception, TelegramUnauthorizedError):
        logger.error(ErrorMessages.UNAUTHORIZED_TOKEN.value)
        raise HTTPException(status_code=401, detail=ErrorMessages.UNAUTHORIZED_TOKEN.value)

    elif isinstance(exception, TelegramForbiddenError):
        logger.warning(ErrorMessages.FORBIDDEN_CHAT.value)
        raise HTTPException(status_code=403, detail=ErrorMessages.FORBIDDEN_CHAT.value)

    elif isinstance(exception, TelegramConflictError):
        logger.error(ErrorMessages.TOKEN_CONFLICT.value)
        raise HTTPException(status_code=409, detail=ErrorMessages.TOKEN_CONFLICT.value)

    elif isinstance(exception, TelegramNotFound):
        logger.info(ErrorMessages.RESOURCE_NOT_FOUND.value)
        raise HTTPException(status_code=404, detail=ErrorMessages.RESOURCE_NOT_FOUND.value)

    elif isinstance(exception, TelegramAPIError):
        logger.error(f"Telegram API error: {exception}")
        raise HTTPException(status_code=500, detail=f"Telegram API error: {exception}")

    elif isinstance(exception, TelegramNetworkError):
        logger.error(f"Network error: {exception}")
        raise HTTPException(status_code=503, detail="Сетевая ошибка Telegram API. Проверьте соединение.")

    # --- fallback ---
    logger.exception(f"Unexpected error while handling {event}: {exception}")
    raise HTTPException(status_code=500, detail=ErrorMessages.UNKNOWN_ERROR_USER.value)
