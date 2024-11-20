import time
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class RateLimitMiddleware(BaseMiddleware):
    RATE_LIMIT = 2  # Лимит времени в секундах

    async def __call__(self, handler, event, data):
        # Определяем user_id только для событий, содержащих пользователя
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            last_time = data.get(f'last_time_{user_id}', 0)
            current_time = time.time()

            if current_time - last_time < self.RATE_LIMIT:
                # Для Message и CallbackQuery используем метод answer
                await event.answer("Слишком много запросов! Попробуйте позже.")
                return

            # Сохраняем последнее время запроса для конкретного пользователя
            data[f'last_time_{user_id}'] = current_time

        # Передаем событие в следующий обработчик
        return await handler(event, data)
