from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineQuery,
    TelegramObject,
)

from app.core.utils.logger_manager import LoggerManager


class CommandLoggingMiddleware(BaseMiddleware):
    """Middleware для логирования команд, callback-кнопок и inline-запросов."""

    def __init__(self, logger: LoggerManager):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        self.logger.debug(f"[CommandLogging] Получен event: {type(event).__name__}")

        # Обработка команд / текстовых сообщений
        if isinstance(event, Message):
            await self._log_message(event)

        # Обработка callback-кнопок
        elif isinstance(event, CallbackQuery):
            await self._log_callback(event)

        # Обработка inline-запросов
        elif isinstance(event, InlineQuery):
            await self._log_inline(event)

        result = await handler(event, data)
        self.logger.debug("[CommandLogging] Обработка завершена")
        return result

    async def _log_message(self, message: Message) -> None:
        """Логирование команд в текстовых сообщениях."""
        chat_id = getattr(message.chat, "id", None)
        user = message.from_user

        if not user or not chat_id:
            self.logger.warning("[CommandLogging] Нет информации о пользователе или чате")
            return

        is_command = (message.text and message.text.startswith("/")) or \
                     (message.caption and message.caption.startswith("/"))

        self.logger.debug(f"[CommandLogging] Chat ID: {chat_id}, User ID: {user.id}")

        if is_command:
            self.logger.info(
                f"📥 Команда: {message.text or message.caption} "
                f"от {user.id} ({user.full_name} | @{user.username or '—'})"
            )

    async def _log_callback(self, cb: CallbackQuery) -> None:
        """Логирование callback-кнопок."""
        user = cb.from_user
        data = cb.data or "<пусто>"
        message_id = getattr(cb.message, "message_id", "—") if cb.message else "—"

        self.logger.info(
            f"🔘 Callback от {user.id} ({user.full_name} | @{user.username or '—'}) | "
            f"Message ID: {message_id} | Data: {data}"
        )

    async def _log_inline(self, iq: InlineQuery) -> None:
        """Логирование inline-запросов."""
        user = iq.from_user
        query = iq.query or "<пусто>"

        self.logger.info(
            f"🔍 Inline-запрос от {user.id} ({user.full_name} | @{user.username or '—'}) | "
            f"Запрос: {query}"
        )
