import asyncio
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from collections import defaultdict
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.last_called = defaultdict(lambda: 0.0)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = getattr(event.from_user, "id", None)
        now = time.monotonic()

        if user_id:
            elapsed = now - self.last_called[user_id]
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
            self.last_called[user_id] = time.monotonic()

        return await handler(event, data)
