from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.core.utils.logger_manager import LoggerManager


class CommandLoggingMiddleware(BaseMiddleware):
    def __init__(self, logger: LoggerManager):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        self.logger.debug(
            f"[CommandLogging] Обработка события: {type(event).__name__}")

        if isinstance(event, Message):
            self.logger.debug(
                f"[CommandLogging] Chat ID: {event.chat.id}, User ID: {event.from_user.id}")

            if event.text and event.text.startswith("/"):
                user = event.from_user
                self.logger.info(
                    f"📥 Команда: {event.text} "
                    f"от {user.id} ({user.full_name} | @{user.username or '—'})"
                )

        result = await handler(event, data)

        self.logger.debug("[CommandLogging] Завершение обработки")

        return result
