import asyncio
from logging import Logger
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message
from typing import Callable, Dict, Any, Awaitable, Optional, Union
from collections import defaultdict
import time
from datetime import timedelta


class SmartRateLimitMiddleware(BaseMiddleware):
    """
    Умный middleware для ограничения частоты запросов с гибридным поведением:
    - Сначала добавляет задержки при частых запросах
    - Затем полностью блокирует при превышении лимита
    - Поддерживает автоматический сброс после периода бездействия
    """
    
    def __init__(
        self,
        logger: Logger,
        rate_limit: float = 1.0,
        max_spam: int = 3,
        cooldown: Optional[Union[float, timedelta]] = None,
        exempt_user_ids: Optional[set[int]] = None
    ):
        """
        :param logger: Логгер для записи событий
        :param rate_limit: Лимит времени между запросами в секундах
        :param max_spam: Максимальное количество быстрых запросов перед блокировкой
        :param cooldown: Время сброса счетчика спама (None для бессрочного)
        :param exempt_user_ids: Пользователи, исключенные из ограничений
        """
        self.rate_limit = rate_limit
        self.max_spam = max_spam
        self.cooldown = cooldown.total_seconds() if isinstance(cooldown, timedelta) else cooldown
        self.exempt_users = exempt_user_ids or set()
        self.logger = logger
        
        # Хранение данных пользователя: last_time, spam_count, last_warning
        self.user_data = defaultdict(lambda: {
            "last_time": 0.0,
            "spam_count": 0,
            "last_warning": 0.0
        })

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = getattr(event.from_user, "id", None)
        if not user_id or user_id in self.exempt_users:
            return await handler(event, data)

        now = time.monotonic()
        user = self.user_data[user_id]
        
        # Сброс счетчика, если прошло время cooldown
        if self.cooldown and (now - user["last_time"] > self.cooldown):
            user["spam_count"] = 0

        # Проверка частоты запросов
        if now - user["last_time"] < self.rate_limit:
            user["spam_count"] += 1
            
            # Логирование предупреждения
            if user["spam_count"] == self.max_spam - 1:
                self.logger.warning(f"User {user_id} approaching rate limit")

            # Блокировка при превышении лимита
            if user["spam_count"] >= self.max_spam:
                # Ограничение частоты предупреждений (не чаще 1 раза в 10 секунд)
                if now - user["last_warning"] > 10:
                    if isinstance(event, (Message, CallbackQuery)):
                        await event.answer(
                            "⚠️ Слишком много запросов! Пожалуйста, подождите...",
                            show_alert=True
                        )
                    user["last_warning"] = now
                return None

            # Добавление задержки
            delay = self.rate_limit - (now - user["last_time"])
            await asyncio.sleep(delay)

        # Обновление времени последнего запроса и сброс счетчика
        user["last_time"] = now
        if user["spam_count"] > 0 and now - user["last_time"] >= self.rate_limit * 2:
            user["spam_count"] = 0

        return await handler(event, data)