from aiogram import Router
from aiogram.exceptions import TelegramRetryAfter, TelegramUnauthorizedError, TelegramForbiddenError, \
    TelegramConflictError, TelegramNotFound, TelegramBadRequest, TelegramAPIError
from aiogram.types import Update

from app.constants import ErrorMessages
from app.utils.logger_instance import app_logger

router = Router()


@router.errors()
async def error_handler(event: Update, *args, **kwargs):
    """
    Унифицированный обработчик ошибок для исключений Telegram API.
    """
    exception = kwargs.get("exception")

    if not exception:
        app_logger.error(ErrorMessages.NO_EXCEPTION_INFO.value, exc_info=True)
        return

    # Карта обработки исключений и соответствующих действий
    exception_map = {
        TelegramRetryAfter: (
            ErrorMessages.FLOOD_CONTROL,
            ErrorMessages.FLOOD_CONTROL,
            "warning",
            {"retry_after": exception.retry_after},
        ),
        TelegramUnauthorizedError: (
            ErrorMessages.UNAUTHORIZED_TOKEN,
            None,
            "error",
            None,
        ),
        TelegramForbiddenError: (
            ErrorMessages.FORBIDDEN_CHAT,
            ErrorMessages.FORBIDDEN_CHAT,
            "warning",
            None,
        ),
        TelegramConflictError: (
            None,
            ErrorMessages.TOKEN_CONFLICT,
            "error",
            None,
        ),
        TelegramNotFound: (
            ErrorMessages.RESOURCE_NOT_FOUND,
            ErrorMessages.RESOURCE_NOT_FOUND,
            "info",
            None,
        ),
        TelegramBadRequest: (
            ErrorMessages.BAD_REQUEST,
            ErrorMessages.BAD_REQUEST,
            "warning",
            {"exception": exception},
        ),
        TelegramAPIError: (
            ErrorMessages.TELEGRAM_API_ERROR,
            ErrorMessages.TELEGRAM_API_ERROR,
            "error",
            {"exception": exception},
        ),
    }

    # Обработка ошибки из карты
    log_message, send_message, log_level, format_data = exception_map.get(type(exception),
                                                                          (None, None, "exception", {}))

    if send_message:
        await event.message.answer(send_message.value.format(**(format_data or {})))

    if log_message:
        log_func = getattr(app_logger, log_level)
        log_func(log_message.value.format(**(format_data or {})))

    # Обработка неизвестных ошибок
    if not log_message and not send_message:
        app_logger.exception(ErrorMessages.UNKNOWN_ERROR_USER.value, exc_info=exception)
        await event.message.answer(ErrorMessages.UNKNOWN_ERROR_USER.value)

    return True  # Чтобы предотвратить дальнейшую обработку ошибок
