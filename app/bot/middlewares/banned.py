import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class BannedCheckMiddleware(BaseMiddleware):

    def __init__(self, logger: Logger):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        if user.is_banned:
            await event.answer("⛔️ Вы заблокированы.")
            return
        return await handler(event, data)
