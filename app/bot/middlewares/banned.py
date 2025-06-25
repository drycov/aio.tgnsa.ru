import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from app.bot.constants.messages import Messages


class BannedCheckMiddleware(BaseMiddleware):
    """
    Middleware для проверки, заблокирован ли пользователь.
    Если пользователь заблокирован — сообщение не обрабатывается.
    """

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
        is_banned = getattr(user, "is_banned", False)
        is_superuser = data.get("is_superuser", False)

        if is_superuser:
            self.logger.debug(f"🔁 Суперпользователь tg_id={tg_id} — игнор блокировки")
            return await handler(event, data)

        if user and is_banned:
            self.logger.warning(f"⛔️ Заблокирован tg_id={tg_id} — доступ запрещён")

            if isinstance(event, Message):
                await event.answer(Messages.YOU_ARE_BANNED.value)
            else:
                self.logger.debug("⚠️ Event не поддерживает .answer(), пропуск уведомления")

            return  # Прекращаем обработку

        # Пользователь не заблокирован
        return await handler(event, data)
