import asyncio
import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Set

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.bot.constants.messages import TFA_MESSAGES
from app.core.config import settings
from app.core.services.tfa import verify_tfa_code


class TfaMiddleware(BaseMiddleware):
    """Middleware для двухфакторной аутентификации (TOTP)."""

    def __init__(self, logger: Logger, timeout: int = 60, cache_ttl: int = 3600):
        self.logger = logger
        self.timeout = timeout
        # кэш верифицированных пользователей: user_id -> expires_at
        self._verified_users: Dict[int, float] = {}
        self.cache_ttl = cache_ttl

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("user")
        tg_id = getattr(user, "tg_id", getattr(user, "id", None))
        username = getattr(user, "username", None)

        if self._is_skip_tfa(user, data):
            return await handler(event, data)

        if self._is_verified(tg_id):
            return await handler(event, data)

        # Промпт пользователю
        try:
            await event.answer(TFA_MESSAGES.get("prompt", "Введите TFA-код"))
        except Exception:
            pass

        # Ожидание кода
        try:
            response: Message = await event.bot.wait_for(
                "message",
                timeout=self.timeout,
                check=lambda m: m.from_user.id == event.from_user.id
                and (m.text and m.text.isdigit()),
            )
        except asyncio.TimeoutError:
            await self._safe_answer(event, TFA_MESSAGES.get("timeout", "⏱ Время вышло"))
            self.logger.warning(f"[TFA] Timeout tg_id={tg_id} ({username})")
            return

        if not getattr(user, "tfa_secret", None):
            await self._safe_answer(event, "⚠️ У вас не настроен TFA")
            self.logger.error(f"[TFA] tg_id={tg_id} ({username}) без tfa_secret")
            return

        if not verify_tfa_code(user.tfa_secret, response.text):
            await self._safe_answer(event, TFA_MESSAGES.get("fail", "❌ Неверный код"))
            self.logger.warning(f"[TFA] Invalid TOTP tg_id={tg_id} ({username})")
            return

        # ✅ Успех
        self._verified_users[tg_id] = time.time() + self.cache_ttl
        await self._safe_answer(event, TFA_MESSAGES.get("success", "✅ Успешная проверка"))
        self.logger.info(f"[TFA] ✅ Verified tg_id={tg_id} ({username})")

        return await handler(event, data)

    def _is_skip_tfa(self, user: Any, data: Dict[str, Any]) -> bool:
        if data.get("is_superuser"):
            self.logger.debug("[TFA] Пропуск для суперпользователя")
            return True
        if not settings.security.TFA_ENABLE:
            return True
        if not user:
            return True
        if not getattr(user, "tfa_enabled", False):
            return True
        return False

    def _is_verified(self, tg_id: int) -> bool:
        """Проверка, есть ли user в кэше и не истёк ли TTL."""
        if not tg_id:
            return False
        expires_at = self._verified_users.get(tg_id)
        if not expires_at:
            return False
        if time.time() > expires_at:
            self._verified_users.pop(tg_id, None)
            return False
        return True

    @staticmethod
    async def _safe_answer(event: Message, text: str) -> None:
        try:
            await event.answer(text)
        except Exception:
            pass
