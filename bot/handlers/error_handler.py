import logging
from aiogram import Router
from aiogram.types import Update
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
    TelegramForbiddenError,
    TelegramConflictError,
    TelegramNotFound,
    TelegramBadRequest,
)
from .error_messages import ErrorMessages  # Импортируем перечисление сообщений

# Создаем маршрутизатор для регистрации обработчиков
router = Router()

# Настройка логирования
logger = logging.getLogger("bot_logger")


@router.errors()
async def error_handler(event: Update, *args, **kwargs):
    """
    Обработчик ошибок для различных исключений, связанных с работой Telegram API.
    """
    exception = kwargs.get("exception")

    if not exception:
        logger.error(ErrorMessages.NO_EXCEPTION_INFO.value)
        return

    # Проверка на конкретные ошибки и логика обработки
    if isinstance(exception, TelegramRetryAfter):
        await event.message.answer(ErrorMessages.FLOOD_CONTROL.value.format(retry_after=exception.retry_after))
        logger.warning(
            ErrorMessages.FLOOD_CONTROL_LOG.value.format(method=exception.method, retry_after=exception.retry_after))

    elif isinstance(exception, TelegramUnauthorizedError):
        logger.error(ErrorMessages.UNAUTHORIZED_TOKEN.value)

    elif isinstance(exception, TelegramForbiddenError):
        logger.warning(ErrorMessages.FORBIDDEN_CHAT.value)
        await event.message.answer(ErrorMessages.FORBIDDEN_CHAT_USER.value)

    elif isinstance(exception, TelegramConflictError):
        logger.error(ErrorMessages.TOKEN_CONFLICT.value)

    elif isinstance(exception, TelegramNotFound):
        await event.message.answer(ErrorMessages.RESOURCE_NOT_FOUND.value)
        logger.info(ErrorMessages.RESOURCE_NOT_FOUND_LOG.value)

    elif isinstance(exception, TelegramBadRequest):
        await event.message.answer(ErrorMessages.BAD_REQUEST.value)
        logger.warning(ErrorMessages.BAD_REQUEST_LOG.value.format(exception=exception))

    elif isinstance(exception, TelegramAPIError):
        logger.error(ErrorMessages.TELEGRAM_API_ERROR.value.format(exception=exception))
        await event.message.answer(ErrorMessages.TELEGRAM_API_USER.value)

    else:
        logger.exception(ErrorMessages.UNKNOWN_ERROR.value, exc_info=exception)
        await event.message.answer(ErrorMessages.UNKNOWN_ERROR_USER.value)

    # Возвращаем True, чтобы обработчик ошибок не вызывал дальнейшую обработку
    return True
