from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserService


class AuthMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        session_maker = data.get("db")
        if session_maker is None:
            self.logger.error(
                "❗️DB session maker not found in middleware context.")
            await event.answer("⚠️ Внутренняя ошибка. Попробуйте позже.")
            return

        tg_id = event.from_user.id

        try:
            # Создаем новую сессию для работы с БД
            async with session_maker() as session:
                user_service = UserService(session)
                user = await user_service.get_user(tg_id)

                # Временно заменяем на заглушку
                # user = None  # Замените на реальный код получения пользователя

                if not user:
                    await event.answer("❌ Пользователь не найден.")
                    return

                data["user"] = user
                return await handler(event, data)

        except Exception as e:
            self.logger.exception(
                f"Ошибка при получении пользователя {tg_id} из БД: {e}")
            await event.answer("⚠️ Ошибка при обращении к базе данных.")
            return
