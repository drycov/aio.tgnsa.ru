import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from loguru import logger


class RoleMiddleware(BaseMiddleware):
    """Middleware that restricts access to handlers based on user roles.

    Only users with roles specified in required_roles are allowed to proceed to the handler.
    """

    def __init__(self, required_roles: list[str], logger: Logger):
        self.logger = logger

        self.required_roles = required_roles

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        if user.role not in self.required_roles:
            await event.answer("⛔️ Недостаточно прав.")
            return
        return await handler(event, data)
