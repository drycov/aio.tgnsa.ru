import asyncio
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from app.core.config import settings
from app.core.services.tfa import verify_tfa_code  # Предполагается наличие TOTP-проверки

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

        user_id = user.id

        # Если TFA отключён глобально — пропускаем
        if not settings.security.TFA_ENABLE:
            return await handler(event, data)

        # Если у пользователя не включён TFA — пропускаем
        if not getattr(user, "tfa_enabled", False):
            return await handler(event, data)

        # Если пользователь уже подтвердил — пропускаем
        if user_id in _verified_users:
            return await handler(event, data)

        await event.answer("🔐 У вас включена двухфакторная авторизация.\nПожалуйста, введите код подтверждения:")

        def check(m: Message) -> bool:
            return m.from_user.id == event.from_user.id and m.text and m.text.isdigit()

        try:
            from aiogram import Dispatcher
            dp: Dispatcher = data["dispatcher"]
            response: Message = await dp.wait_for("message", timeout=self.timeout, check=check)
        except asyncio.TimeoutError:
            await event.answer("⏱️ Время ожидания кода истекло. Повторите попытку позже.")
            self.logger.warning(f"TFA timeout for user_id={user_id}")
            return

        # Проверка кода (предположительно — через TOTP-секрет)
        if not verify_tfa_code(user.tfa_secret, response.text):
            await event.answer("❌ Неверный код двухфакторной авторизации.")
            self.logger.warning(f"TFA failed for user_id={user_id}")
            return

        # Пометить как подтверждённого
        _verified_users.add(user_id)
        await event.answer("✅ Успешная авторизация. Продолжаем.")
        return await handler(event, data)
