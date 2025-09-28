import asyncio
import time
from collections import defaultdict
from datetime import timedelta
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

try:
    from prometheus_client import Counter
    RATE_LIMIT_HITS = Counter(
        "tg_rate_limit_hits_total",
        "Number of rate-limit triggers",
        ["scope"]
    )
except ImportError:
    RATE_LIMIT_HITS = None


class SmartRateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов с гибридной стратегией:
    - Задержки при превышении лимита
    - Блокировка при избыточной активности
    """

    def __init__(
        self,
        logger: Logger,
        rate_limit: float = 1.0,
        max_spam: int = 3,
        cooldown: Optional[Union[float, timedelta]] = None,
        exempt_user_ids: Optional[set[int]] = None,
        warn_cooldown: float = 10.0,
        enable_chat_scope: bool = False,
    ):
        self.logger = logger
        self.rate_limit = rate_limit
        self.max_spam = max_spam
        self.cooldown = (
            cooldown.total_seconds()
            if isinstance(cooldown, timedelta)
            else cooldown or (5 * rate_limit)
        )
        self.exempt_users = exempt_user_ids or set()
        self.warn_cooldown = warn_cooldown
        self.enable_chat_scope = enable_chat_scope

        # Структуры для отслеживания активности
        self.user_data = defaultdict(
            lambda: {"last_time": 0.0, "spam_count": 0, "last_warning": 0.0}
        )
        if self.enable_chat_scope:
            self.chat_data = defaultdict(
                lambda: {"last_time": 0.0, "spam_count": 0, "last_warning": 0.0}
            )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = getattr(event.from_user, "id", None)
        chat_id = getattr(getattr(event, "chat", None), "id", None)

        if not user_id or user_id in self.exempt_users:
            return await handler(event, data)

        # Проверяем лимиты на уровне юзера
        if not await self._check_scope("user", user_id, event):
            return None

        # Проверяем лимиты на уровне чата
        if self.enable_chat_scope and chat_id:
            if not await self._check_scope("chat", chat_id, event):
                return None

        return await handler(event, data)

    async def _check_scope(self, scope: str, entity_id: int, event: TelegramObject) -> bool:
        """Проверка и обновление состояния для конкретного scope (user/chat)."""
        now = time.monotonic()
        storage = self.user_data if scope == "user" else self.chat_data
        entity = storage[entity_id]
        elapsed = now - entity["last_time"]

        # Сброс после паузы
        if elapsed > self.cooldown:
            entity["spam_count"] = 0

        # Проверка частоты
        if elapsed < self.rate_limit:
            entity["spam_count"] += 1

            if entity["spam_count"] >= self.max_spam:
                if now - entity["last_warning"] > self.warn_cooldown:
                    self.logger.warning(
                        f"🚫 {scope.capitalize()} {entity_id} превысил лимит запросов"
                    )
                    await self._answer_too_many_requests(event)
                    entity["last_warning"] = now
                if RATE_LIMIT_HITS:
                    RATE_LIMIT_HITS.labels(scope).inc()
                return False

            elif entity["spam_count"] == self.max_spam - 1:
                self.logger.debug(f"⚠️ {scope.capitalize()} {entity_id} приближается к лимиту")

            # Искусственная задержка
            delay = self.rate_limit - elapsed
            await asyncio.sleep(delay)

        entity["last_time"] = now
        return True

    @staticmethod
    async def _answer_too_many_requests(event: TelegramObject) -> None:
        """Отправка уведомления пользователю о превышении лимита."""
        text = "⚠️ Слишком много запросов. Попробуйте позже."

        try:
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
        except Exception:
            pass  # Игнорировать любые ошибки Telegram
