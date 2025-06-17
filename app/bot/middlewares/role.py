from functools import partial
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.bot.constants.messages import AUTH_MESSAGES


class RoleMiddleware(BaseMiddleware):
    """Оптимизированная проверка ролей с кешированием и улучшенной обработкой ошибок."""

    def __init__(self, required_roles: Set[str], logger: Logger):
        self.required_roles = required_roles
        self.logger = logger
        self._get_user_id = partial(self._extract_user_id, logger=logger)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Пропуск для суперпользователей
        if data.get('is_superuser'):
            return await handler(event, data)
        
        user_id = self._get_user_id(event, data)
        self.logger.debug(event)
        self.logger.debug(data)
        if user_id is None:
            return await self._deny_access(event, "User ID not found")

        user = data.get("user")
        
        if not user:
            return await self._deny_access(event, "User data missing")

        if user_roles := self._extract_user_roles(user):
            return (
                await handler(event, data) if user_roles.intersection(self.required_roles) else await self._deny_access(
                                    event,
                                    f"Access denied for {user_id}: {user_roles} not in {self.required_roles}",
                                )
            )
        else:
            return await self._deny_access(event, f"No roles for user {user_id}")

    async def _deny_access(self, event: TelegramObject, reason: str) -> None:
        """Унифицированная обработка отказа в доступе."""
        self.logger.warning(reason)
        if isinstance(event, (Message, CallbackQuery)):
            await event.answer("⛔ Доступ запрещен")

    @staticmethod
    def _extract_user_id(event: TelegramObject, data: Dict[str, Any], logger: Logger) -> Optional[int]:
        """Унифицированное извлечение user_id с обработкой ошибок."""
        try:
            user = event.from_user or data.get("user")
            return getattr(user, "tg_id", None) or getattr(user, "id", None)
        except Exception as e:
            logger.debug(f"User ID extraction error: {e}")
            return None

    @staticmethod
    def _extract_user_roles(user: Any) -> Set[str]:
        """Извлечение ролей пользователя с обработкой разных форматов."""
        try:
            if hasattr(user, "roles"):
                return {role.name if hasattr(role, "name") else str(role) for role in user.roles}
            return {user.role} if hasattr(user, "role") else set()
        except Exception:
            return set()
