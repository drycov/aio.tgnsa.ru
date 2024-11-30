import time

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from bot.bot_instance import storage
from bot.utils.logger_instance import app_logger


class UserActivityMiddleware(BaseMiddleware):
    INACTIVITY_THRESHOLD = 300  # Порог неактивности в секундах (5 минут)

    async def __call__(self, handler, event, data):
        # Проверяем, содержит ли событие данные о пользователе
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            current_time = int(time.time())
            last_activity_key = f"fsm:{user_id}:last_activity"

            # Асинхронный вызов для получения времени последней активности
            last_activity = await storage.get(last_activity_key)
            if last_activity:
                last_activity = int(last_activity)
                inactivity_period = current_time - last_activity

                if inactivity_period > self.INACTIVITY_THRESHOLD:
                    app_logger.info(
                        f"User {user_id} признан неактивным. Время неактивности: {inactivity_period} секунд."
                    )
                    await event.answer("Вы были неактивны, сессия была приостановлена.")
                else:
                    app_logger.info(f"User {user_id} активен. Время неактивности: {inactivity_period} секунд.")
            else:
                app_logger.info(f"User {user_id} активен впервые.")

            # Асинхронное обновление времени последней активности и установка времени хранения данных
            await storage.set(last_activity_key, current_time, ex=3600)  # Данные удалятся через 1 час неактивности

        # Передаем обработку события дальше
        return await handler(event, data)

    @staticmethod
    async def is_user_active(user_id: int) -> bool:
        """
        Асинхронная проверка, является ли пользователь активным.
        """
        last_activity_key = f"fsm:{user_id}:last_activity"
        last_activity = await storage.get(last_activity_key)
        if last_activity:
            inactivity_period = int(time.time()) - int(last_activity)
            return inactivity_period <= UserActivityMiddleware.INACTIVITY_THRESHOLD
        return False
