import asyncio
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Message, TelegramObject

from app.bot.constants.messages import TFA_MESSAGES
from app.core.config import settings
from app.core.services.tfa import verify_tfa_code

# Кэш подтверждённых пользователей
_verified_users = set()


class TfaMiddleware(BaseMiddleware):
    """Middleware для двухфакторной аутентификации (TOTP)."""

    def __init__(self, logger: Logger, timeout: int = 60):
        self.logger = logger
        self.timeout = timeout

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("user")
        dispatcher: Dispatcher = data.get("dispatcher")
        user_id = getattr(user, "id", None)
        tg_id = getattr(user, "tg_id", user_id)

        if self._is_skip_tfa(user, data):
            return await handler(event, data)

        if user_id in _verified_users:
            return await handler(event, data)

        if dispatcher is None:
            self.logger.error(
                f"[TFA] Dispatcher not found in context for tg_id={tg_id}"
            )
            return await handler(event, data)

        await event.answer(TFA_MESSAGES["prompt"])

        try:
            response: Message = await dispatcher.wait_for(
                "message",
                timeout=self.timeout,
                check=lambda m: m.from_user.id == event.from_user.id
                and m.text
                and m.text.isdigit(),
            )
        except asyncio.TimeoutError:
            await event.answer(TFA_MESSAGES["timeout"])
            self.logger.warning(f"[TFA] Timeout for tg_id={tg_id}")
            return

        if not verify_tfa_code(user.tfa_secret, response.text):
            await event.answer(TFA_MESSAGES["fail"])
            self.logger.warning(f"[TFA] Invalid TOTP for tg_id={tg_id}")
            return

        _verified_users.add(user_id)
        self.logger.info(f"[TFA] ✅ Verified tg_id={tg_id}")
        await event.answer(TFA_MESSAGES["success"])
        return await handler(event, data)

    def _is_skip_tfa(self, user: Any, data: Dict[str, Any]) -> bool:
        """Проверка условий, при которых TFA можно пропустить."""
        if data.get("is_superuser"):
            self.logger.debug("[TFA] Пропуск для суперпользователя")
            return True

        if not settings.security.TFA_ENABLE:
            self.logger.debug("[TFA] Глобально отключён")
            return True

        if not user:
            self.logger.warning("[TFA] User not found")
            return True

        if not getattr(user, "tfa_enabled", False):
            self.logger.debug("[TFA] Пользователь не активировал TFA")
            return True

        return False
