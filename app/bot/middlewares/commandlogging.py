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
    """Middleware для логирования команд, callback-кнопок, inline-запросов и действий меню."""

    def __init__(self, logger: LoggerManager):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        self.logger.debug(f"[CommandLogging] ▶️ Event: {type(event).__name__}")

        if isinstance(event, Message):
            await self._log_message(event)
        elif isinstance(event, CallbackQuery):
            await self._log_callback(event)
        elif isinstance(event, InlineQuery):
            await self._log_inline(event)

        result = await handler(event, data)
        self.logger.debug("[CommandLogging] ✅ Обработка завершена")
        return result

    async def _log_message(self, message: Message) -> None:
        chat = message.chat
        user = message.from_user

        if not user or not chat:
            self.logger.warning("[CommandLogging] ⚠️ Отсутствует chat или user")
            return

        text = message.text or message.caption or ""
        is_command = text.startswith("/")
        is_menu = text.lower() in ("menu", "меню", "главное меню")

        log_prefix = (
            "📥 Команда" if is_command else "📩 Меню" if is_menu else "✉️ Сообщение"
        )
        chat_type = chat.type
        lang = user.language_code or "—"

        self.logger.info(
            f"[CommandLogging] "
            f"{log_prefix} | Chat[{chat_type}] {chat.id} | User {user.id} "
            f"({user.full_name} | @{user.username or '—'}) | "
            f"Lang: {lang} | Text: {text}"
        )

    async def _log_callback(self, cb: CallbackQuery) -> None:
        user = cb.from_user
        message = cb.message
        data = cb.data or "<пусто>"

        is_menu = data.lower() in ("menu", "меню", "main_menu", "open_menu")

        msg_info = (
            f"{message.chat.id}:{message.message_id}"
            if message and message.chat
            else "—"
        )
        log_prefix = "🔘 Callback-Меню" if is_menu else "🔘 Callback"

        self.logger.info(
            f"{log_prefix} | Msg: {msg_info} | User {user.id} "
            f"({user.full_name} | @{user.username or '—'}) | Data: {data}"
        )

    async def _log_inline(self, iq: InlineQuery) -> None:
        user = iq.from_user
        query = iq.query or "<пусто>"
        is_menu = query.lower() in ("menu", "меню")

        log_prefix = "🔍 Inline-Меню" if is_menu else "🔍 Inline"

        self.logger.info(
            f"{log_prefix} | User {user.id} ({user.full_name} | @{user.username or '—'}) | "
            f"Query: {query}"
        )
