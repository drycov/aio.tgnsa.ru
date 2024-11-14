from typing import Union

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.models import User
from app.utils.logger_instance import app_logger
from config import Config


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Union[Message, CallbackQuery], data):
        state: FSMContext = data.get("state")  # Получаем состояние FSM
        # Проверка, содержит ли событие данные о пользователе
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            stored_data = await state.get_data()
            token = stored_data.get("token")
            print(
                f"user_id: {user_id}, stored_data: {stored_data}, token: {token}"
            )
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

            # Проверка JWT токена, если он был сохранен ранее
            if token:
                decoded_data = User.decode_jwt(token, Config.SECRET_KEY)
                if not decoded_data:
                    await event.answer("Недействительный или истекший токен. Пожалуйста, войдите заново.")
                    app_logger.warning(f"Неверный JWT токен для пользователя с tg_id {user_id}.")
                    return
                # Отображаем декодированные данные, если нужно
                print(decoded_data)

            # Если токена нет, создаем и сохраняем его в state
            if not token:
                new_token = User.generate_jwt(user_id, Config.SECRET_KEY)
                await state.update_data(token=new_token)

        # Передаем обработку события дальше, если авторизация прошла успешно
        return await handler(event, data)
