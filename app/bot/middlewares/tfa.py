import asyncio
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.bot.constants.messages import TFA_MESSAGES
from app.core.config import settings
from app.core.services.tfa import \
    verify_tfa_code  # Предполагается наличие TOTP-проверки

# Кеш временного хранения подтверждённых пользователей
_verified_users = set()


class TfaMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger, timeout: int = 60):
        self.logger = logger
        self.timeout = timeout

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("user")
        if not user:
            self.logger.warning("User not found in context data")
            return await handler(event, data)

        user_id = getattr(user, "id", None)
        tg_id = getattr(user, "tg_id", user_id)

        if data.get("is_superuser"):
            self.logger.debug(
                f"🔁 Суперпользователь tg_id={tg_id} — пропуск TFA.")
            return await handler(event, data)

        if not settings.security.TFA_ENABLE:
            return await handler(event, data)

        if not getattr(user, "tfa_enabled", False):
            return await handler(event, data)

        if user_id in _verified_users:
            return await handler(event, data)

        await event.answer(TFA_MESSAGES["prompt"])

        def check(m: Message) -> bool:
            return m.from_user.id == event.from_user.id and m.text and m.text.isdigit()

        try:
            from aiogram import Dispatcher
            dp = data["dispatcher"]
            response: Message = await dp.wait_for("message", timeout=self.timeout, check=check)
        except asyncio.TimeoutError:
            await event.answer(TFA_MESSAGES["timeout"])
            self.logger.warning(f"TFA timeout for user_id={user_id}")
            return

        if not verify_tfa_code(user.tfa_secret, response.text):
            await event.answer(TFA_MESSAGES["fail"])
            self.logger.warning(f"TFA failed for user_id={user_id}")
            return

        _verified_users.add(user_id)
        await event.answer(TFA_MESSAGES["success"])
        return await handler(event, data)
