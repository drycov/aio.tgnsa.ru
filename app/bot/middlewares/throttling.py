import asyncio
import time
from collections import defaultdict
from datetime import timedelta
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


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

        self.user_data = defaultdict(lambda: {
            "last_time": 0.0,
            "spam_count": 0,
            "last_warning": 0.0
        })

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = getattr(event.from_user, "id", None)

        if not user_id or user_id in self.exempt_users:
            return await handler(event, data)

        now = time.monotonic()
        user = self.user_data[user_id]
        elapsed = now - user["last_time"]

        # Сброс после бездействия
        if elapsed > self.cooldown:
            user["spam_count"] = 0

        # Проверка частоты
        if elapsed < self.rate_limit:
            user["spam_count"] += 1

            if user["spam_count"] >= self.max_spam:
                if now - user["last_warning"] > 10:
                    self.logger.warning(f"🚫 Пользователь {user_id} превысил лимит запросов")
                    await self._answer_too_many_requests(event)
                    user["last_warning"] = now
                return None

            # Предупреждение перед блокировкой
            elif user["spam_count"] == self.max_spam - 1:
                self.logger.debug(f"⚠️ Пользователь {user_id} приближается к лимиту")

            # Искусственная задержка
            delay = self.rate_limit - elapsed
            await asyncio.sleep(delay)

        # Обновление состояния
        user["last_time"] = now

        return await handler(event, data)

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
