from typing import Union
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from bot.models import User
from bot.utils.logger_instance import app_logger
from config import Config


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Union[Message, CallbackQuery], data):
        state: FSMContext = data.get("state")  # Получаем состояние FSM

        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            stored_data = await state.get_data()
            token = stored_data.get("token")

            # Log the user details (instead of print, use logger)
            app_logger.info(f"user_id: {user_id}, stored_data: {stored_data}, token: {token}")

            # Проверяем, существует ли пользователь
            user = await self.get_user_by_tg_id(user_id)
            if not user:
                await event.answer("Доступ запрещен. Пожалуйста, зарегистрируйтесь.")
                app_logger.warning(f"Неавторизованный доступ от пользователя с tg_id {user_id}.")
                return

            # Проверка, активирован ли пользователь
            if not user.is_allowed_user():
                await event.answer("Ваш доступ ограничен. Обратитесь к администратору.")
                app_logger.info(f"Ограниченный доступ для пользователя с tg_id {user_id}.")
                return

            # Обработка JWT токена
            if token:
                if not await self.validate_token(token, user_id):
                    await event.answer("Недействительный или истекший токен. Пожалуйста, войдите заново.")
                    return

            # Если токена нет, создаем и сохраняем его в state
            elif not token:
                await self.generate_and_store_token(user_id, state)

        # Передаем обработку события дальше, если авторизация прошла успешно
        return await handler(event, data)

    async def get_user_by_tg_id(self, tg_id: int) -> Union[User, None]:
        """
        Получает пользователя по tg_id.
        """
        try:
            user = await User.get_by_tg_id(tg_id)
            return user
        except Exception as e:
            app_logger.error(f"Ошибка при получении пользователя с tg_id {tg_id}: {e}")
            return None

    async def validate_token(self, token: str, user_id: int) -> bool:
        """
        Проверяет валидность JWT токена.
        """
        decoded_data = User.decode_jwt(token, Config.SECRET_KEY)
        if not decoded_data:
            app_logger.warning(f"Неверный или истекший JWT токен для пользователя с tg_id {user_id}.")
            return False
        app_logger.info(f"JWT токен валиден для пользователя с tg_id {user_id}.")
        return True

    async def generate_and_store_token(self, user_id: int, state: FSMContext) -> None:
        """
        Генерирует новый JWT токен и сохраняет его в state.
        """
        new_token = User.generate_jwt(user_id, Config.SECRET_KEY)
        await state.update_data(token=new_token)
        app_logger.info(f"Новый JWT токен сгенерирован и сохранен для пользователя с tg_id {user_id}.")
