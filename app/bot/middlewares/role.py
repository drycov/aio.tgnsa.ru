from functools import partial
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.bot.constants.messages import AUTH_MESSAGES


class RoleMiddleware(BaseMiddleware):
    """Проверка ролей с кэшированием и надёжной авторизацией."""

    def __init__(self, required_roles: set[str], logger: Logger):
        self.required_roles = required_roles
        self.logger = logger

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if data.get("is_superuser"):
            return await handler(event, data)

        user = data.get("user")
        if not user:
            return await self._deny("User not found", event)

        user_id = self._get_user_id(event, data)
        if not user_id:
            return await self._deny("User ID missing", event)

        # Кэшируем роли в data, избегаем повторных вычислений
        if "user_roles" not in data:
            data["user_roles"] = {r.name for r in getattr(user, "roles", [])}
        roles: set[str] = data["user_roles"]

        if roles & self.required_roles:
            return await handler(event, data)
        else:
            return await self._deny(f"Access denied: {roles} not in {self.required_roles}", event)

    async def _deny(self, reason: str, event: TelegramObject):
        self.logger.warning(reason)
        if isinstance(event, (Message, CallbackQuery)):
            await event.answer(AUTH_MESSAGES["no_permission"])
