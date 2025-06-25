import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.core.utils.logger_manager import LoggerManager


class ProfilerMiddleware(BaseMiddleware):
    """
    Middleware для профилирования времени обработки события.
    """

    def __init__(self, logger: Logger | LoggerManager, warn_threshold: float = 1.0):
        """
        :param logger: Экземпляр логгера
        :param warn_threshold: Порог в секундах, после которого лог пишется как warning
        """
        self.logger = logger
        self.warn_threshold = warn_threshold

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_type = type(event).__name__
        start = time.perf_counter()

        try:
            result = await handler(event, data)
        finally:
            duration = time.perf_counter() - start
            user_id, chat_id = self._extract_ids(event)

            msg = (
                f"⏱ {event_type:<18} | "
                f"{duration:.3f} сек. | "
                f"user_id={user_id or '-'} chat_id={chat_id or '-'}"
            )

            logger: Logger | LoggerManager | None = data.get("logger", self.logger)

            if duration >= self.warn_threshold:
                getattr(logger, "warning", self.logger.warning)(msg)
            else:
                getattr(logger, "debug", self.logger.debug)(msg)

        return result

    @staticmethod
    def _extract_ids(event: TelegramObject) -> tuple[Any, Any]:
        """Попытка извлечь user_id и chat_id из разных типов событий."""
        user_id = chat_id = None

        if isinstance(event, Message):
            user_id = getattr(event.from_user, "id", None)
            chat_id = getattr(event.chat, "id", None)
        elif isinstance(event, CallbackQuery):
            user_id = getattr(event.from_user, "id", None)
            chat_id = getattr(event.message.chat, "id", None)

        return user_id, chat_id
