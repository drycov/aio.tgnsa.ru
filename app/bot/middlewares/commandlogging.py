import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineQuery,
    TelegramObject,
    ChatMemberUpdated,
)
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from app.core.utils.logger_manager import LoggerManager


class CommandLoggingMiddleware(BaseMiddleware):
    """Middleware для централизованного логирования событий Telegram."""

    def __init__(self, logger: LoggerManager, warn_threshold: float = 2.0):
        self.logger = logger
        self.warn_threshold = warn_threshold

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start = time.perf_counter()
        event_type = type(event).__name__

        try:
            # Логируем входящее событие
            await self._log_event(event)

            result = await handler(event, data)
            return result

        except TelegramRetryAfter as e:
            self.logger.warning(f"[CommandLogging] ⏳ Flood control: retry after {e.retry_after}s")
            raise
        except TelegramAPIError as e:
            self.logger.error(f"[CommandLogging] ❌ Telegram API error: {e}")
            raise
        finally:
            duration = time.perf_counter() - start
            if duration > self.warn_threshold:
                self.logger.warning(f"[CommandLogging] ⏱ {event_type} обработан за {duration:.2f}s")
            else:
                self.logger.debug(f"[CommandLogging] ⏱ {event_type} {duration:.2f}s")

    async def _log_event(self, event: TelegramObject) -> None:
        if isinstance(event, Message):
            await self._log_message(event)
        elif isinstance(event, CallbackQuery):
            await self._log_callback(event)
        elif isinstance(event, InlineQuery):
            await self._log_inline(event)
        elif isinstance(event, ChatMemberUpdated):
            await self._log_member_update(event)
        else:
            self.logger.debug(f"[CommandLogging] 📡 Unsupported event: {type(event).__name__}")

    async def _log_message(self, message: Message) -> None:
        user, chat = message.from_user, message.chat
        if not user or not chat:
            return

        text = message.text or message.caption or ""
        log_prefix = "📥 Команда" if text.startswith("/") else "✉️ Сообщение"
        self.logger.info(
            f"{log_prefix} | Chat[{chat.type}] {chat.id} | "
            f"User {user.id} ({user.full_name} | @{user.username or '—'}) | "
            f"Lang: {user.language_code or '—'} | Text: {text}"
        )

    async def _log_callback(self, cb: CallbackQuery) -> None:
        user, msg, data = cb.from_user, cb.message, cb.data or "<пусто>"
        msg_info = f"{msg.chat.id}:{msg.message_id}" if msg and msg.chat else "—"
        self.logger.info(
            f"🔘 Callback | Msg {msg_info} | "
            f"User {user.id} ({user.full_name} | @{user.username or '—'}) | "
            f"Data: {data}"
        )

    async def _log_inline(self, iq: InlineQuery) -> None:
        user, query = iq.from_user, iq.query or "<пусто>"
        self.logger.info(
            f"🔍 Inline | User {user.id} ({user.full_name} | @{user.username or '—'}) | "
            f"Query: {query}"
        )

    async def _log_member_update(self, ev: ChatMemberUpdated) -> None:
        user = ev.from_user
        self.logger.info(
            f"👥 MemberUpdate | Chat {ev.chat.id} | User {user.id} "
            f"({user.full_name} | @{user.username or '—'}) | "
            f"Old: {ev.old_chat_member.status} → New: {ev.new_chat_member.status}"
        )
