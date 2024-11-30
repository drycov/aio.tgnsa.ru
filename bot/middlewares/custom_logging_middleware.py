import json

from aiogram import BaseMiddleware
from aiogram.types import Update, Message

from bot.utils.logger_instance import app_logger


class CustomLoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Update):
            await self.log_update(event)

        result = await handler(event, data)

        if isinstance(result, Message):
            await self.log_message(result)

        return result

    async def log_update(self, update: Update):
        update_type = update.event_type
        update_id = update.update_id

        log_data = {
            "update_id": update_id,
            "update_type": update_type,
        }

        if update.message:
            log_data["message"] = {
                "message_id": update.message.message_id,
                "from_user": update.message.from_user.id,
                "chat": update.message.chat.id,
                "text": update.message.text[:100] if update.message.text else None  # Truncate long messages
            }
        elif update.callback_query:
            log_data["callback_query"] = {
                "id": update.callback_query.id,
                "from_user": update.callback_query.from_user.id,
                "data": update.callback_query.data
            }

        app_logger.info(f"Received update: {json.dumps(log_data, ensure_ascii=False)}")

    async def log_message(self, message: Message):
        log_data = {
            "message_id": message.message_id,
            "chat": message.chat.id,
            "text": message.text[:100] if message.text else None  # Truncate long messages
        }

        app_logger.info(f"Sent message: {json.dumps(log_data, ensure_ascii=False)}")
