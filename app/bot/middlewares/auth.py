from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants.messages import Messages
from app.core.db import get_session
from app.exceptions.exceptions import UserBannedError, UserNotFoundError
from app.services.user import UserSearchField, UserService


class AuthMiddleware(BaseMiddleware):
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

        tg_id = event.from_user.id

        session_gen = get_session()
        session: AsyncSession = await anext(session_gen)

        try:
            user_service = UserService(session)

            # Пропуск полной аутентификации, если суперпользователь уже авторизован вручную
            if data.get("is_superuser"):
                user = await user_service.get_user(tg_id, UserSearchField.TG_ID)
                data["user"] = user
                data["session"] = session
                self.logger.debug(
                    f"🔁 Суперпользователь — пропуск проверки на бан и регистрацию для tg_id={tg_id}")
                return await handler(event, data)

            # Стандартная логика авторизации
            user = await user_service.get_user(tg_id, UserSearchField.TG_ID)

            if user.is_banned:
                raise UserBannedError()

            data["user"] = user
            data["session"] = session

            self.logger.info(
                f"✅ Authenticated user: tg_id={tg_id}, id={user.id}")
            return await handler(event, data)

        except UserNotFoundError:
            self.logger.warning(f"UserNotFoundError for tg_id={tg_id}")
            await event.answer(Messages.USER_NOT_FOUND.value)

        except UserBannedError:
            self.logger.info(f"Banned user: tg_id={tg_id}")
            await event.answer(Messages.ACCCOUNT_BANNED.value)

        except Exception as e:
            self.logger.exception(
                f"Unhandled exception for tg_id={tg_id}: {e}")
            await event.answer(Messages.INTERNAL_ERROR.value)

        finally:
            await session_gen.aclose()
