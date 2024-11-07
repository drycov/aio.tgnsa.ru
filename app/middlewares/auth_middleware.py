from typing import Union

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from app.models import User
from app.utils.logger_instance import app_logger


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Union[Message, CallbackQuery], data):
        # Проверка, содержит ли событие данные о пользователе
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

            # Получаем данные пользователя из Firebase
            user = User.get_by_tg_id(user_id)

            # Проверяем, существует ли пользователь
            if not user:
                await event.answer("Доступ запрещен. Пожалуйста, зарегистрируйтесь.")
                app_logger.warning(f"Неавторизованный доступ от пользователя с tg_id {user_id}.")
                return

            # Проверяем, активирован ли пользователь
            if not user.is_allowed_user():
                await event.answer("Ваш доступ ограничен. Обратитесь к администратору.")
                app_logger.info(f"Ограниченный доступ для пользователя с tg_id {user_id}.")
                return

            # Проверяем, является ли пользователь администратором, если это требуется
            if hasattr(data, "admin_required") and data["admin_required"] and not user.is_admin_user():
                await event.answer("Доступ запрещен. Только администраторы могут выполнять эту операцию.")
                app_logger.info(f"Попытка неадминистративного доступа от пользователя с tg_id {user_id}.")
                return

        # Передаем обработку события дальше, если авторизация прошла успешно
        return await handler(event, data)
