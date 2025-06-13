from logging import Logger
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class TfaMiddleware(BaseMiddleware):

    def __init__(self, logger: Logger):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        if not user.tfa_verified:
            await event.answer("🔐 Подтвердите вход через двухфакторную авторизацию.")
            return
        return await handler(event, data)
