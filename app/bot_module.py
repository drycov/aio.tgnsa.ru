# bot_module.py
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from app import handlers
from app.bot_instance import dp, bot
from app.constants import Messages
from app.middlewares import CustomLoggingMiddleware, RateLimitMiddleware, UserActivityMiddleware, AuthMiddleware
from app.utils.logger_instance import app_logger  # Предполагаем, что app_logger уже инициализирован
from config import Config

dp.update.middleware(RateLimitMiddleware())
dp.update.middleware(UserActivityMiddleware())
dp.update.middleware(AuthMiddleware())


def setup_bot():
    """
    Настройка бота и регистрация обработчиков.
    """
    # Подключение маршрутизатора команд
    router = handlers.get_handlers_router()
    dp.include_router(router)
    dp.update.middleware(CallbackAnswerMiddleware())  # Aiogram 3.x использует новый способ для middleware
    Config.DEBUG = True
    if Config.DEBUG:
        dp.update.middleware(CustomLoggingMiddleware())


async def start_bot(on_startup=None):
    """
    Запускает бота и начинает обработку сообщений.
    """
    # Удаление вебхука и начало поллинга
    app_logger.info(Messages.DELETE_WEBHOOK.value)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), on_startup=on_startup)
    app_logger.info(Messages.START_BOT.value)


async def graceful_shutdown():
    """
    Функция для корректного завершения работы бота.
    """
    app_logger.info(Messages.SHUTDOWN_BOT.value)
    await dp.storage.close()
    await bot.session.close()
    app_logger.info(Messages.BOT_SHUTDOWN_COMPLETE.value)
