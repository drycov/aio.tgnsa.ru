from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class SuperuserBypassMiddleware(BaseMiddleware):
    """Middleware, пропускающий суперпользователей без дополнительных проверок."""

    def __init__(self, superusers: list[int], logger):
        self.superusers = {int(uid) for uid in (superusers or [])}
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user or data.get("user")
        tg_id = getattr(user, "tg_id", None) or getattr(user, "id", None)
        event_type = type(event).__name__

        if tg_id in self.superusers:
            self.logger.info(
                f"🔓 Суперпользователь tg_id={tg_id} — пропуск всех проверок.")
            data["is_superuser"] = True
            return await handler(event, data)
        self.logger.debug(
            f"👥 Пользователь tg_id={tg_id} ({event_type}) — продолжение цепочки middleware.")
        return await handler(event, data)
