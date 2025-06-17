from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants.messages import Messages
from app.core.db import get_session
from app.exceptions.exceptions import UserBannedError, UserNotFoundError
from app.services.user import UserSearchField, UserService


class AuthMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger, dispatcher: Dispatcher):
        self.logger = logger
        self.dispatcher = dispatcher
        

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

            # Пропуск проверки, если суперпользователь уже авторизован
            if data.get("is_superuser"):
                user = await user_service.get_user(tg_id, UserSearchField.TG_ID)
                data["user"] = user
                data["session"] = session
                self.logger.debug(
                    f"🔁 Суперпользователь — пропуск проверки на бан и регистрацию для tg_id={tg_id}")
                return await handler(event, data)

            # Основная авторизация
            try:
                user = await user_service.get_user(tg_id, UserSearchField.TG_ID)
           # Вставка внутри блока except UserNotFoundError:
            except UserNotFoundError:
                self.logger.info(f"👤 Новый пользователь: начало регистрации tg_id={tg_id}")
                
                # Привязываем FSM-состояние
                if isinstance(event, Message):
                    from app.bot.handlers.main_handlers.registration_handler import start_registration
                    from aiogram.fsm.context import FSMContext
    
                    # FSMContext создаётся из Dispatcher в обычных условиях. Здесь нужно получить вручную:
                    from aiogram import Dispatcher
                    dispatcher: Dispatcher = data["dispatcher"]
                    fsm_context: FSMContext = dispatcher.fsm.get_context(event.chat.id, event.from_user.id)

                    # Запуск регистрации
                    await start_registration(event, fsm_context)
                    return  # Выход, не вызываем handler


            if user.is_banned:
                raise UserBannedError()

            data["user"] = user
            data["session"] = session

            self.logger.info(
                f"✅ Авторизован: tg_id={tg_id}, user_id={user.id}")
            return await handler(event, data)

        except UserBannedError:
            self.logger.info(f"🚫 Забанен: tg_id={tg_id}")
            await event.answer(Messages.ACCCOUNT_BANNED.value)

        except Exception as e:
            self.logger.exception(
                f"❌ Необработанная ошибка tg_id={tg_id}: {e}")
            await event.answer(Messages.INTERNAL_ERROR.value)

        finally:
            await session_gen.aclose()
