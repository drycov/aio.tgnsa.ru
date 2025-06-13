from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserSearchField, UserService
from app.exceptions.exceptions import UserBannedError, UserNotFoundError


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для аутентификации пользователя по Telegram ID.
    Проверяет существование пользователя и статус бана.
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Optional[Any]:
        if not isinstance(event, Message):
            return await handler(event, data)

        session_gen = data.get("db")
        if session_gen is None:
            self.logger.error("❗️ DB session generator not found in middleware context.")
            await event.answer("⚠️ Внутренняя ошибка. Попробуйте позже.")
            return None

        tg_id = event.from_user.id
        session: Optional[AsyncSession] = None

        try:
            # Получаем сессию из генератора
            session = await session_gen.__anext__()
            user_service = UserService(session)

            user = await user_service.get_user(tg_id, UserSearchField.TG_ID)

            if user is None:
                self.logger.warning(f"User with tg_id={tg_id} not found.")
                await event.answer("❌ Пользователь не найден.")
                return None

            if user.is_banned:
                self.logger.info(f"User with tg_id={tg_id} is banned.")
                await event.answer("🚫 Ваш аккаунт заблокирован.")
                return None

            self.logger.info(f"✅ Authenticated user: tg_id={tg_id}, id={user.id}")
            data["user"] = user

            return await handler(event, data)

        except UserNotFoundError:
            self.logger.warning(f"UserNotFoundError for tg_id={tg_id}")
            await event.answer("❌ Пользователь не найден.")
            return None

        except UserBannedError:
            self.logger.info(f"UserBannedError for tg_id={tg_id}")
            await event.answer("🚫 Ваш аккаунт заблокирован.")
            return None

        except Exception as exc:
            self.logger.exception(f"Unhandled exception in AuthMiddleware for tg_id={tg_id}: {exc}")
            await event.answer("⚠️ Внутренняя ошибка. Попробуйте позже.")
            return None

        finally:
            if session:
                await session.close()
