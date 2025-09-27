from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery, TelegramObject

from app.bot.constants.messages import Messages


class BannedCheckMiddleware(BaseMiddleware):
    """
    Middleware для проверки блокировки пользователя.
    - Если пользователь заблокирован → сообщение не обрабатывается.
    - Суперпользователи игнорируют проверку.
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("user")
        tg_id = getattr(user, "tg_id", None)
        username = getattr(user, "username", None)
        full_name = getattr(user, "full_name", None)

        is_banned = getattr(user, "is_banned", False)
        is_superuser = data.get("is_superuser", False)

        # 🔁 Суперпользователь игнорирует блокировки
        if is_superuser:
            self.logger.debug(f"🔁 SUPERUSER tg_id={tg_id} ({username}) — игнор блокировки")
            return await handler(event, data)

        # 🚫 Заблокирован
        if user and is_banned:
            ban_reason = getattr(user, "ban_reason", "—")
            self.logger.warning(
                f"⛔️ Заблокирован tg_id={tg_id} ({username or '—'} | {full_name or '—'}) "
                f"— причина: {ban_reason}"
            )

            text = getattr(Messages.YOU_ARE_BANNED, "value", "⛔️ Вы заблокированы. Обратитесь к администратору.")

            try:
                if isinstance(event, Message):
                    await event.answer(text)
                elif isinstance(event, CallbackQuery):
                    await event.answer(text, show_alert=True)
                elif isinstance(event, InlineQuery):
                    # inline не поддерживает прямой answer — просто логируем
                    self.logger.debug("⚠️ InlineQuery не поддерживает уведомление о бане")
            except Exception as e:
                self.logger.error(f"❌ Ошибка при уведомлении о бане tg_id={tg_id}: {e}")

            return None  # ❌ прекращаем обработку

        # ✅ Пользователь не заблокирован
        return await handler(event, data)
