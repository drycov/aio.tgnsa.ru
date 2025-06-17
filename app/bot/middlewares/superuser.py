from functools import partial
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class SuperuserBypassMiddleware(BaseMiddleware):
    """Middleware для пропуска суперпользователей с кешированием и оптимизированными проверками."""

    def __init__(self, superusers: Set[int], logger: Logger):
        self.superusers = superusers
        self.logger = logger
        self._get_user_id = partial(self._extract_user_id, logger=logger)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = self._get_user_id(event, data)
        if user_id is None:
            return await handler(event, data)

        if user_id in self.superusers:
            data['is_superuser'] = True
            self.logger.debug(f"Superuser access granted: {user_id}")
            return await handler(event, data)

        return await handler(event, data)

    @staticmethod
    def _extract_user_id(event: TelegramObject, data: Dict[str, Any], logger: Logger) -> Optional[int]:
        """Унифицированное извлечение user_id с обработкой ошибок."""
        try:
            user = event.from_user or data.get("user")
            return getattr(user, "tg_id", None) or getattr(user, "id", None)
        except Exception as e:
            logger.debug(f"User ID extraction error: {e}")
            return None
