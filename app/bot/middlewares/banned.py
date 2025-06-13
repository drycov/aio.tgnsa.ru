import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.bot.constants.messages import Messages


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
        tg_id = getattr(user, "tg_id", None)

        if data.get("is_superuser"):
            self.logger.debug(
                f"🔁 Суперпользователь — пропуск проверки блокировки для tg_id={tg_id}")
            return await handler(event, data)

        if user and getattr(user, "is_banned", False):
            self.logger.warning(
                f"⛔️ Заблокированный пользователь: tg_id={tg_id}")
            await event.answer(Messages.YOU_ARE_BANNED.value)
            return

        return await handler(event, data)
